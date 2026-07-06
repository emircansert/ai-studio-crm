import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AITool,
    AuditLog,
    BorusanCompany,
    Contact,
    Event,
    EventParticipant,
    EventTag,
    ImportBatch,
    ImportCandidate,
    ImportRow,
    ImportSheet,
    ImportWarning,
    Note,
    Opportunity,
    Organization,
    OrganizationBorusanFit,
    OrganizationTag,
    Status,
    Tag,
)


ENTITY_ORGANIZATION = "ORGANIZATION"
ENTITY_CONTACT = "CONTACT"
ENTITY_FIT = "ORGANIZATION_BORUSAN_FIT"
ENTITY_OPPORTUNITY = "OPPORTUNITY"
ENTITY_EVENT = "EVENT"
ENTITY_EVENT_PARTICIPANT = "EVENT_PARTICIPANT"
ENTITY_AI_TOOL = "AI_TOOL"
ENTITY_NOTE = "NOTE"

APPROVED = "APPROVED"
PENDING = "PENDING"
REJECTED = "REJECTED"
SKIPPED = "SKIPPED"


class ImportCandidateService:
    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir
        self.status_mapping = self._load_yaml("status_mapping.yml")
        self.borusan_mapping = self._load_yaml("borusan_company_mapping.yml")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        with (self.config_dir / filename).open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _first_value(self, values: dict[str, Any], *column_names: str) -> Any:
        """Return the first non-empty value among alternative header names.

        Workbook versions have used both Turkish and English headers for the
        same logical column, so every lookup checks all known variants.
        """
        for column_name in column_names:
            value = values.get(column_name)
            if value not in (None, ""):
                return value
        return None

    def generate_candidates(self, db: Session, batch_id: UUID) -> dict[str, Any]:
        batch = db.get(ImportBatch, batch_id)
        if batch is None:
            raise ValueError("Import batch not found")
        if batch.status == "COMMITTED":
            raise ValueError("Committed batches cannot be regenerated")

        existing_count = db.execute(
            select(func.count()).select_from(ImportCandidate).where(ImportCandidate.import_batch_id == batch_id)
        ).scalar_one()
        if existing_count:
            return self.build_candidate_preview(db, batch_id)

        sheets = db.execute(
            select(ImportSheet).where(ImportSheet.import_batch_id == batch_id).order_by(ImportSheet.sheet_name)
        ).scalars().all()
        rows_by_entity: dict[str, list[ImportRow]] = defaultdict(list)
        for sheet in sheets:
            rows = db.execute(
                select(ImportRow).where(ImportRow.import_sheet_id == sheet.id).order_by(ImportRow.excel_row_number)
            ).scalars().all()
            rows_by_entity[sheet.detected_entity or "UNKNOWN"].extend(rows)

        existing_orgs = db.execute(select(Organization)).scalars().all()
        existing_by_domain: dict[str, list[Organization]] = defaultdict(list)
        existing_by_name: dict[str, list[Organization]] = defaultdict(list)
        for organization in existing_orgs:
            if organization.website_domain:
                existing_by_domain[organization.website_domain.lower()].append(organization)
            existing_by_name[organization.normalized_name].append(organization)

        startup_rows = rows_by_entity.get("STARTUP_LIBRARY", [])
        startup_domain_names: dict[str, set[str]] = defaultdict(set)
        startup_name_rows: dict[str, list[ImportRow]] = defaultdict(list)
        for row in startup_rows:
            values = row.cleaned_values or {}
            name = self._normalize_name(values.get("Startup"))
            domain = self._extract_domain(values.get("Website"))
            if name:
                startup_name_rows[name].append(row)
            if domain and name:
                startup_domain_names[domain].add(name)

        org_candidates_by_name: dict[str, ImportCandidate] = {}
        org_candidates_by_domain: dict[str, ImportCandidate] = {}

        for row in startup_rows:
            candidate = self._candidate_from_startup_row(
                db,
                batch,
                row,
                existing_by_domain,
                existing_by_name,
                startup_domain_names,
                startup_name_rows,
            )
            if candidate is None:
                continue
            db.add(candidate)
            db.flush()
            org_data = candidate.candidate_data.get("organization", {})
            normalized_name = org_data.get("normalized_name")
            website_domain = org_data.get("website_domain")
            if normalized_name:
                org_candidates_by_name[normalized_name] = candidate
            if website_domain:
                org_candidates_by_domain[website_domain] = candidate
            self._add_startup_dependents(db, batch, row, candidate)

        for row in rows_by_entity.get("NETWORK", []):
            candidate = self._candidate_from_network_row(db, batch, row, existing_by_name)
            if candidate is None:
                continue
            db.add(candidate)
            db.flush()
            org_data = candidate.candidate_data.get("organization", {})
            normalized_name = org_data.get("normalized_name")
            if normalized_name:
                org_candidates_by_name.setdefault(normalized_name, candidate)
            self._add_network_dependents(db, batch, row, candidate)

        for row in rows_by_entity.get("POC_OPPORTUNITIES", []):
            self._add_poc_candidates(db, batch, row, org_candidates_by_name, existing_by_name)

        for row in rows_by_entity.get("EVENTS", []):
            self._add_event_candidates(db, batch, row)

        for row in rows_by_entity.get("AI_TOOLS", []):
            self._add_ai_tool_candidate(db, batch, row)

        batch.status = "MAPPED"
        batch.workbook_metadata = {
            **(batch.workbook_metadata or {}),
            "candidate_generation": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "idempotency": "Existing candidates are reused on subsequent generation calls.",
            },
        }
        db.add(batch)
        db.commit()
        return self.build_candidate_preview(db, batch_id)

    def build_candidate_preview(self, db: Session, batch_id: UUID) -> dict[str, Any]:
        batch = db.get(ImportBatch, batch_id)
        if batch is None:
            raise ValueError("Import batch not found")

        candidates = db.execute(
            select(ImportCandidate)
            .where(ImportCandidate.import_batch_id == batch_id)
            .order_by(ImportCandidate.entity_type, ImportCandidate.created_at)
        ).scalars().all()

        entity_counts = Counter(candidate.entity_type for candidate in candidates)
        action_counts = Counter(candidate.action_type for candidate in candidates)
        validation_counts = Counter(candidate.validation_status for candidate in candidates)
        decision_counts = Counter(candidate.decision_status for candidate in candidates)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        needs_review: list[dict[str, Any]] = []
        for candidate in candidates:
            serialized = self._serialize_candidate(candidate)
            if len(grouped[candidate.entity_type]) < 25:
                grouped[candidate.entity_type].append(serialized)
            if candidate.validation_status in {"NEEDS_REVIEW", "ERROR"} or candidate.decision_status == PENDING:
                needs_review.append(serialized)

        return {
            "batch": {
                "id": str(batch.id),
                "status": batch.status,
                "original_filename": batch.original_filename,
                "file_sha256": batch.file_sha256,
            },
            "candidate_counts_by_entity_type": dict(entity_counts),
            "action_counts": dict(action_counts),
            "validation_counts": dict(validation_counts),
            "decision_counts": dict(decision_counts),
            "candidates_by_entity_type": dict(grouped),
            "needs_review": needs_review[:100],
            "duplicate_match_summary": self._duplicate_match_summary(candidates),
            "warnings": self._candidate_warning_summary(candidates),
            "can_commit": self._can_commit(candidates, batch.status),
        }

    def update_decision(
        self,
        db: Session,
        candidate_id: UUID,
        *,
        decision_status: str,
        decision_reason: str | None,
    ) -> ImportCandidate:
        candidate = db.get(ImportCandidate, candidate_id)
        if candidate is None:
            raise ValueError("Import candidate not found")
        normalized_status = decision_status.upper()
        if normalized_status not in {APPROVED, REJECTED, SKIPPED}:
            raise ValueError("decision_status must be APPROVED, REJECTED, or SKIPPED")
        if candidate.validation_status == "ERROR" and normalized_status == APPROVED:
            raise ValueError("ERROR candidates cannot be approved")
        candidate.decision_status = normalized_status
        candidate.decision_reason = decision_reason
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    def commit(self, db: Session, batch_id: UUID, actor_user_id: UUID | None) -> dict[str, Any]:
        batch = db.get(ImportBatch, batch_id)
        if batch is None:
            raise ValueError("Import batch not found")
        if batch.status == "COMMITTED":
            raise ValueError("Import batch is already committed")

        candidates = db.execute(
            select(ImportCandidate).where(ImportCandidate.import_batch_id == batch_id)
        ).scalars().all()
        if not candidates:
            raise ValueError("Generate candidates before committing")

        structural_errors = db.execute(
            select(ImportWarning).where(
                ImportWarning.import_batch_id == batch_id,
                ImportWarning.severity == "ERROR",
                ImportWarning.code.in_(["COLUMN_TYPE_MISMATCH", "MISSING_REQUIRED_COLUMN"]),
            )
        ).scalars().all()
        if structural_errors:
            messages = "; ".join(sorted({warning.message for warning in structural_errors}))
            raise ValueError(
                "The workbook structure looks misaligned and committing would corrupt data. "
                f"Fix the file or the column mapping first: {messages}"
            )

        blocking = [
            candidate
            for candidate in candidates
            if candidate.validation_status in {"ERROR", "NEEDS_REVIEW"} and candidate.decision_status == PENDING
        ]
        if blocking:
            raise ValueError("Resolve NEEDS_REVIEW and ERROR candidates before commit")

        approved = [candidate for candidate in candidates if candidate.decision_status == APPROVED]
        entity_map: dict[str, UUID] = {}
        counts: Counter[str] = Counter()

        try:
            for candidate in approved:
                if candidate.entity_type == ENTITY_ORGANIZATION:
                    organization_id = self._commit_organization(db, candidate)
                    if organization_id:
                        entity_map[str(candidate.id)] = organization_id
                        if candidate.action_type != "MATCH":
                            counts[ENTITY_ORGANIZATION] += 1

            for candidate in approved:
                if candidate.entity_type == ENTITY_CONTACT:
                    if self._commit_contact(db, candidate, entity_map):
                        counts[ENTITY_CONTACT] += 1
                elif candidate.entity_type == ENTITY_FIT:
                    if self._commit_fit(db, candidate, entity_map):
                        counts[ENTITY_FIT] += 1
                elif candidate.entity_type == ENTITY_EVENT:
                    event_id = self._commit_event(db, candidate)
                    if event_id:
                        entity_map[str(candidate.id)] = event_id
                        counts[ENTITY_EVENT] += 1
                elif candidate.entity_type == ENTITY_AI_TOOL:
                    if self._commit_ai_tool(db, candidate):
                        counts[ENTITY_AI_TOOL] += 1

            for candidate in approved:
                if candidate.entity_type == ENTITY_OPPORTUNITY:
                    opportunity_id = self._commit_opportunity(db, candidate, entity_map)
                    if opportunity_id:
                        entity_map[str(candidate.id)] = opportunity_id
                        counts[ENTITY_OPPORTUNITY] += 1
                elif candidate.entity_type == ENTITY_EVENT_PARTICIPANT:
                    if self._commit_event_participant(db, candidate, entity_map):
                        counts[ENTITY_EVENT_PARTICIPANT] += 1

            for candidate in approved:
                if candidate.entity_type == ENTITY_NOTE:
                    if self._commit_note(db, candidate, entity_map):
                        counts[ENTITY_NOTE] += 1

            batch.status = "COMMITTED"
            db.add(batch)
            self._audit(
                db,
                action="IMPORT_COMMIT",
                entity_type="ImportBatch",
                actor_user_id=actor_user_id,
                entity_id=batch.id,
                after_data={"committed_counts": dict(counts)},
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {"batch_id": str(batch.id), "status": batch.status, "committed_counts": dict(counts)}

    def _candidate_from_startup_row(
        self,
        db: Session,
        batch: ImportBatch,
        row: ImportRow,
        existing_by_domain: dict[str, list[Organization]],
        existing_by_name: dict[str, list[Organization]],
        startup_domain_names: dict[str, set[str]],
        startup_name_rows: dict[str, list[ImportRow]],
    ) -> ImportCandidate | None:
        values = row.cleaned_values or {}
        name = values.get("Startup")
        normalized_name = self._normalize_name(name)
        if not normalized_name:
            return self._candidate(
                batch,
                row,
                ENTITY_ORGANIZATION,
                "SKIP",
                {},
                row.raw_values,
                "ERROR",
                PENDING,
                reason="Missing startup name",
            )

        website_url = values.get("Website")
        website_domain = self._extract_domain(website_url)
        category_tags = self._split_tags(values.get("Category"), "CATEGORY")
        vertical_text = values.get("Vertical")
        organization = {
            "name": name,
            "normalized_name": normalized_name,
            "organization_type": "STARTUP",
            "organization_subtype": "AI_STARTUP",
            "category_code": self._category_code(category_tags),
            "category_label": category_tags[0]["label"] if category_tags else None,
            "vertical_text": vertical_text,
            "website_url": website_url,
            "website_domain": website_domain,
            "geography_text": self._first_value(values, "Geography", "Coğrafya"),
            "source_text": self._first_value(values, "Source", "Kaynak"),
            "added_by_text": values.get("Added By"),
            "solution_summary": values.get("Solution / Use-case"),
            "last_contact_date": self._iso_date_string_or_none(values.get("Last Contact")),
            "lifecycle_status_code": self._status_code(
                self._first_value(values, "Process Status (1 to 7)", "Status"), "company_status"
            ),
            "tags": category_tags + self._split_tags(vertical_text, "VERTICAL"),
        }

        action = "CREATE"
        validation = "VALID"
        decision = APPROVED
        match_entity_id = None
        reason = None

        if website_domain and len(startup_domain_names.get(website_domain, set())) > 1:
            action, validation, decision = "NEEDS_REVIEW", "NEEDS_REVIEW", PENDING
            reason = "Duplicate website domain appears with different normalized names in the workbook."
        elif normalized_name and not website_domain and len(startup_name_rows.get(normalized_name, [])) > 1:
            action, validation, decision = "NEEDS_REVIEW", "NEEDS_REVIEW", PENDING
            reason = "Duplicate normalized name with missing website."
        elif website_domain and existing_by_domain.get(website_domain):
            matches = existing_by_domain[website_domain]
            if len(matches) == 1:
                action, validation, decision = "MATCH", "VALID", APPROVED
                match_entity_id = matches[0].id
            else:
                action, validation, decision = "NEEDS_REVIEW", "NEEDS_REVIEW", PENDING
                reason = "Multiple existing organizations share this website domain."
        elif existing_by_name.get(normalized_name):
            matches = existing_by_name[normalized_name]
            if len(matches) == 1 and website_domain:
                action, validation, decision = "MATCH", "VALID", APPROVED
                match_entity_id = matches[0].id
            else:
                action, validation, decision = "NEEDS_REVIEW", "NEEDS_REVIEW", PENDING
                reason = "Existing organization name match requires review."

        return self._candidate(
            batch,
            row,
            ENTITY_ORGANIZATION,
            action,
            {"organization": organization, "source_entity": "STARTUP_LIBRARY", "reason": reason},
            row.raw_values,
            validation,
            decision,
            match_entity_type=ENTITY_ORGANIZATION if match_entity_id else None,
            match_entity_id=match_entity_id,
        )

    def _add_startup_dependents(
        self,
        db: Session,
        batch: ImportBatch,
        row: ImportRow,
        organization_candidate: ImportCandidate,
    ) -> None:
        values = row.cleaned_values or {}
        org_ref = str(organization_candidate.id)
        contact_text = self._first_value(values, "Contact Person", "Kontak Kişisi")
        if contact_text:
            db.add(
                self._candidate(
                    batch,
                    row,
                    ENTITY_CONTACT,
                    "CREATE",
                    {
                        "organization_candidate_id": org_ref,
                        "contact": self._contact_data(contact_text),
                    },
                    row.raw_values,
                    "VALID",
                    APPROVED,
                )
            )
        for column_name, code in self._borusan_fit_columns().items():
            raw_value = values.get(column_name)
            if self._is_truthy(raw_value):
                db.add(
                    self._candidate(
                        batch,
                        row,
                        ENTITY_FIT,
                        "CREATE",
                        {
                            "organization_candidate_id": org_ref,
                            "borusan_company_code": code,
                            "fit_level": "RELEVANT",
                            "source": "IMPORT",
                            "raw_value": str(raw_value),
                        },
                        row.raw_values,
                        "VALID",
                        APPROVED,
                    )
                )
        note_body = self._first_value(values, "Notes / Comments", "Notlar / Yorumlar")
        if note_body:
            db.add(self._note_candidate(batch, row, org_ref, ENTITY_ORGANIZATION, note_body))

    def _candidate_from_network_row(
        self,
        db: Session,
        batch: ImportBatch,
        row: ImportRow,
        existing_by_name: dict[str, list[Organization]],
    ) -> ImportCandidate | None:
        values = row.cleaned_values or {}
        name = values.get("Institution")
        normalized_name = self._normalize_name(name)
        if not normalized_name:
            return None
        relationship_code = self._status_code(values.get("Relationship"), "network_relationship")
        organization = {
            "name": name,
            "normalized_name": normalized_name,
            "organization_type": "NETWORK_INSTITUTION",
            "organization_subtype": values.get("Type"),
            "geography_text": values.get("Geography"),
            "added_by_text": self._first_value(values, "Added By / Contact Owner", "Ekleyen / Görüşen"),
            "relationship_status_code": relationship_code,
            "tags": self._split_tags(values.get("Expertise"), "EXPERTISE"),
        }
        action, validation, decision = "CREATE", "VALID", APPROVED
        match_entity_id = None
        reason = None
        matches = existing_by_name.get(normalized_name, [])
        if matches:
            network_matches = [item for item in matches if item.organization_type == "NETWORK_INSTITUTION"]
            if len(network_matches) == 1 and len(matches) == 1:
                action = "MATCH"
                match_entity_id = network_matches[0].id
            else:
                action, validation, decision = "NEEDS_REVIEW", "NEEDS_REVIEW", PENDING
                reason = "Network institution has the same name as an existing non-network organization."
        return self._candidate(
            batch,
            row,
            ENTITY_ORGANIZATION,
            action,
            {"organization": organization, "source_entity": "NETWORK", "reason": reason},
            row.raw_values,
            validation,
            decision,
            match_entity_type=ENTITY_ORGANIZATION if match_entity_id else None,
            match_entity_id=match_entity_id,
        )

    def _add_network_dependents(self, db: Session, batch: ImportBatch, row: ImportRow, organization_candidate: ImportCandidate) -> None:
        values = row.cleaned_values or {}
        org_ref = str(organization_candidate.id)
        contact_text = values.get("Contact Person")
        if contact_text:
            db.add(
                self._candidate(
                    batch,
                    row,
                    ENTITY_CONTACT,
                    "CREATE",
                    {"organization_candidate_id": org_ref, "contact": self._contact_data(contact_text)},
                    row.raw_values,
                    "VALID",
                    APPROVED,
                )
            )
        note_body = values.get("Notes")
        if note_body:
            db.add(self._note_candidate(batch, row, org_ref, ENTITY_ORGANIZATION, note_body))

    def _add_poc_candidates(
        self,
        db: Session,
        batch: ImportBatch,
        row: ImportRow,
        org_candidates_by_name: dict[str, ImportCandidate],
        existing_by_name: dict[str, list[Organization]],
    ) -> None:
        values = row.cleaned_values or {}
        startup_name = values.get("Startup")
        normalized_name = self._normalize_name(startup_name)
        org_candidate = org_candidates_by_name.get(normalized_name or "")
        existing_org = None
        if not org_candidate and normalized_name:
            matches = existing_by_name.get(normalized_name, [])
            if len(matches) == 1:
                existing_org = matches[0]
        if not org_candidate and not existing_org and normalized_name:
            org_candidate = self._candidate(
                batch,
                row,
                ENTITY_ORGANIZATION,
                "NEEDS_REVIEW",
                {
                    "organization": {
                        "name": startup_name,
                        "normalized_name": normalized_name,
                        "organization_type": "STARTUP",
                        "organization_subtype": "AI_STARTUP",
                    },
                    "source_entity": "POC_OPPORTUNITIES",
                    "reason": "PoC startup was not found in Startup Library or existing organizations.",
                },
                row.raw_values,
                "NEEDS_REVIEW",
                PENDING,
            )
            db.add(org_candidate)
            db.flush()
            org_candidates_by_name[normalized_name] = org_candidate

        # "Business Unit" is the primary (left) table of the PoC sheet; "Şirket" is the
        # legacy header and also appears in the sheet's unrelated right-hand block, so
        # "Business Unit" must win when both are present.
        company_code = self._borusan_company_code(self._first_value(values, "Business Unit", "Şirket"))
        validation = "VALID" if company_code else "NEEDS_REVIEW"
        decision = APPROVED if company_code else PENDING
        topic = self._first_value(values, "Topic", "Konu")
        title = topic or f"PoC - {startup_name or 'Unknown startup'}"
        data = {
            "organization_candidate_id": str(org_candidate.id) if org_candidate else None,
            "organization_id": str(existing_org.id) if existing_org else None,
            "borusan_company_code": company_code,
            "opportunity": {
                "title": str(title)[:255],
                "opportunity_type": "POC",
                "stage": self._status_code(
                    self._first_value(values, "Status", "Son Durum"), "opportunity_stage"
                )
                or "DISCUSSIONS_ONGOING",
                "topic": topic,
                "terms_text": self._first_value(values, "PoC Terms", "POC Şartları"),
                "last_contact_date": self._iso_date_string_or_none(
                    self._first_value(values, "Last Contact", "Son Görüşme")
                ),
            },
            "reason": None if company_code else "Borusan company could not be mapped.",
        }
        opportunity_candidate = self._candidate(
            batch,
            row,
            ENTITY_OPPORTUNITY,
            "CREATE",
            data,
            row.raw_values,
            validation,
            decision,
        )
        db.add(opportunity_candidate)
        db.flush()
        note_body = self._first_value(values, "Notes", "Notlar")
        if note_body:
            db.add(self._note_candidate(batch, row, str(opportunity_candidate.id), ENTITY_OPPORTUNITY, note_body))

    def _add_event_candidates(self, db: Session, batch: ImportBatch, row: ImportRow) -> None:
        values = row.cleaned_values or {}
        name = self._first_value(values, "Event Name", "Etkinlik Adı")
        if not name:
            return
        date_value = values.get("Date")
        starts_on = self._iso_date_string_or_none(date_value)
        location = self._first_value(values, "Location", "Lokasyon")
        area = self._first_value(values, "Domain", "Alan")
        event_candidate = self._candidate(
            batch,
            row,
            ENTITY_EVENT,
            "CREATE",
            {
                "event": {
                    "name": name,
                    "starts_on": starts_on,
                    "ends_on": None,
                    "date_text": None if starts_on else date_value,
                    "location_text": location or "Unknown",
                    "geography_text": self._event_geography(location),
                    "area_text": area,
                    "ai_program_relevance": self._status_code(values.get("AI Program Relevance"), "ratings") or "UNKNOWN",
                    "value_creation_potential": self._status_code(
                        self._first_value(values, "Value Creation Potential", "Değer yaratma Opsiyonu"), "ratings"
                    )
                    or "UNKNOWN",
                    "comments": self._first_value(values, "Comments", "Yorumlar"),
                    "tags": self._split_tags(area, "EVENT_AREA")
                    + self._split_tags(self._first_value(values, "Category", "Kategori"), "EVENT_CATEGORY"),
                }
            },
            row.raw_values,
            "VALID",
            APPROVED,
        )
        db.add(event_candidate)
        db.flush()
        participant_role = self._first_value(values, "Recommended Attendee", "Katılımcı")
        participant_name = self._first_value(values, "Attendee Name", "Katılımcı İsmi")
        participant_note = self._first_value(values, "Attendee Note", "Katılımcı Notu")
        if participant_role or participant_name or participant_note:
            db.add(
                self._candidate(
                    batch,
                    row,
                    ENTITY_EVENT_PARTICIPANT,
                    "CREATE",
                    {
                        "event_candidate_id": str(event_candidate.id),
                        "participant": {
                            "participant_role": participant_role or "ATTENDEE",
                            "participant_name": participant_name,
                            "participant_note": participant_note,
                        },
                    },
                    row.raw_values,
                    "VALID",
                    APPROVED,
                )
            )

    def _add_ai_tool_candidate(self, db: Session, batch: ImportBatch, row: ImportRow) -> None:
        values = row.cleaned_values or {}
        name = values.get("Tool Name")
        if not name:
            return
        db.add(
            self._candidate(
                batch,
                row,
                ENTITY_AI_TOOL,
                "CREATE",
                {
                    "ai_tool": {
                        "name": name,
                        "category_text": values.get("Category"),
                        "solution_summary": values.get("Solution"),
                        "notes": self._first_value(values, "Notes", "Notlar"),
                    }
                },
                row.raw_values,
                "VALID",
                APPROVED,
            )
        )

    def _candidate(
        self,
        batch: ImportBatch,
        row: ImportRow | None,
        entity_type: str,
        action_type: str,
        candidate_data: dict[str, Any],
        raw_source: dict[str, Any] | None,
        validation_status: str,
        decision_status: str,
        *,
        match_entity_type: str | None = None,
        match_entity_id: UUID | None = None,
        reason: str | None = None,
    ) -> ImportCandidate:
        if reason:
            candidate_data = {**candidate_data, "reason": reason}
        return ImportCandidate(
            import_batch_id=batch.id,
            import_row_id=row.id if row else None,
            entity_type=entity_type,
            action_type=action_type,
            match_entity_type=match_entity_type,
            match_entity_id=match_entity_id,
            candidate_data=candidate_data,
            raw_source=raw_source,
            validation_status=validation_status,
            decision_status=decision_status,
        )

    def _note_candidate(
        self,
        batch: ImportBatch,
        row: ImportRow,
        entity_candidate_id: str,
        entity_type: str,
        body: str,
    ) -> ImportCandidate:
        return self._candidate(
            batch,
            row,
            ENTITY_NOTE,
            "CREATE",
            {
                "entity_candidate_id": entity_candidate_id,
                "entity_type": entity_type,
                "note": {"note_type": "IMPORT_NOTE", "body": body},
            },
            row.raw_values,
            "VALID",
            APPROVED,
        )

    def _commit_organization(self, db: Session, candidate: ImportCandidate) -> UUID | None:
        data = candidate.candidate_data.get("organization") or {}
        if candidate.action_type == "MATCH" and candidate.match_entity_id:
            existing = db.get(Organization, candidate.match_entity_id)
            if existing:
                self._fill_existing_organization_missing(existing, data)
                db.add(existing)
            return candidate.match_entity_id
        if not data.get("name") or not data.get("normalized_name"):
            return None
        existing = self._find_existing_organization(db, data)
        if existing:
            self._fill_existing_organization_missing(existing, data)
            candidate.match_entity_type = ENTITY_ORGANIZATION
            candidate.match_entity_id = existing.id
            db.add(existing)
            db.add(candidate)
            return existing.id
        organization = Organization(
            name=data["name"],
            normalized_name=data["normalized_name"],
            organization_type=data.get("organization_type") or "STARTUP",
            organization_subtype=data.get("organization_subtype"),
            category_code=data.get("category_code"),
            category_label=data.get("category_label"),
            vertical_text=data.get("vertical_text"),
            website_url=data.get("website_url"),
            website_domain=data.get("website_domain"),
            geography_text=data.get("geography_text"),
            source_text=data.get("source_text"),
            added_by_text=data.get("added_by_text"),
            solution_summary=data.get("solution_summary"),
            lifecycle_status_id=self._status_id(db, data.get("lifecycle_status_code"), "company_status"),
            relationship_status_id=self._status_id(db, data.get("relationship_status_code"), "network_relationship"),
            last_contact_date=self._iso_date_or_none(data.get("last_contact_date")),
            raw_import_ref=candidate.import_row_id,
        )
        db.add(organization)
        db.flush()
        candidate.match_entity_type = ENTITY_ORGANIZATION
        candidate.match_entity_id = organization.id
        self._commit_organization_tags(db, organization.id, data.get("tags") or [])
        self._audit(
            db,
            action="IMPORT_CREATE",
            entity_type=ENTITY_ORGANIZATION,
            entity_id=organization.id,
            after_data=data,
        )
        return organization.id

    def _fill_existing_organization_missing(self, organization: Organization, data: dict[str, Any]) -> None:
        for field_name in [
            "category_code",
            "category_label",
            "vertical_text",
            "added_by_text",
            "source_text",
            "solution_summary",
            "geography_text",
        ]:
            if not getattr(organization, field_name) and data.get(field_name):
                setattr(organization, field_name, data[field_name])
        if not organization.last_contact_date and data.get("last_contact_date"):
            organization.last_contact_date = self._iso_date_or_none(data.get("last_contact_date"))

    def _find_existing_organization(self, db: Session, data: dict[str, Any]) -> Organization | None:
        domain = data.get("website_domain")
        if domain:
            result = db.execute(select(Organization).where(Organization.website_domain == domain)).scalars().all()
            if len(result) == 1:
                return result[0]
        normalized_name = data.get("normalized_name")
        if normalized_name:
            result = db.execute(select(Organization).where(Organization.normalized_name == normalized_name)).scalars().all()
            if len(result) == 1:
                return result[0]
        return None

    def _commit_contact(self, db: Session, candidate: ImportCandidate, entity_map: dict[str, UUID]) -> bool:
        data = candidate.candidate_data
        organization_id = self._resolve_organization_id(db, data, entity_map)
        if not organization_id:
            return False
        contact = data.get("contact") or {}
        email = contact.get("email")
        if email:
            existing = db.execute(
                select(Contact).where(Contact.organization_id == organization_id, Contact.email == email)
            ).scalar_one_or_none()
            if existing:
                return False
        db.add(
            Contact(
                organization_id=organization_id,
                full_name=contact.get("full_name"),
                email=email,
                raw_contact_text=contact.get("raw_contact_text"),
                contact_source="IMPORT",
            )
        )
        return True

    def _commit_fit(self, db: Session, candidate: ImportCandidate, entity_map: dict[str, UUID]) -> bool:
        organization_id = self._resolve_organization_id(db, candidate.candidate_data, entity_map)
        company = self._borusan_company(db, candidate.candidate_data.get("borusan_company_code"))
        if not organization_id or not company:
            return False
        existing = db.execute(
            select(OrganizationBorusanFit).where(
                OrganizationBorusanFit.organization_id == organization_id,
                OrganizationBorusanFit.borusan_company_id == company.id,
            )
        ).scalar_one_or_none()
        if existing:
            return False
        db.add(
            OrganizationBorusanFit(
                organization_id=organization_id,
                borusan_company_id=company.id,
                fit_level=candidate.candidate_data.get("fit_level") or "RELEVANT",
                source="IMPORT",
                raw_value=candidate.candidate_data.get("raw_value"),
            )
        )
        return True

    def _commit_opportunity(self, db: Session, candidate: ImportCandidate, entity_map: dict[str, UUID]) -> UUID | None:
        organization_id = self._resolve_organization_id(db, candidate.candidate_data, entity_map)
        company = self._borusan_company(db, candidate.candidate_data.get("borusan_company_code"))
        data = candidate.candidate_data.get("opportunity") or {}
        if not organization_id or not company:
            return None
        opportunity = Opportunity(
            title=data.get("title") or "Imported PoC opportunity",
            organization_id=organization_id,
            borusan_company_id=company.id,
            opportunity_type=data.get("opportunity_type") or "POC",
            stage=data.get("stage") or "DISCUSSIONS_ONGOING",
            topic=data.get("topic"),
            terms_text=data.get("terms_text"),
            last_contact_date=self._iso_date_or_none(data.get("last_contact_date")),
        )
        db.add(opportunity)
        db.flush()
        candidate.match_entity_type = ENTITY_OPPORTUNITY
        candidate.match_entity_id = opportunity.id
        self._audit(db, action="IMPORT_CREATE", entity_type=ENTITY_OPPORTUNITY, entity_id=opportunity.id, after_data=data)
        return opportunity.id

    def _commit_event(self, db: Session, candidate: ImportCandidate) -> UUID | None:
        data = candidate.candidate_data.get("event") or {}
        if not data.get("name"):
            return None
        event = Event(
            name=data["name"],
            starts_on=self._iso_date_or_none(data.get("starts_on")),
            ends_on=self._iso_date_or_none(data.get("ends_on")),
            date_text=data.get("date_text"),
            location_text=data.get("location_text") or "Unknown",
            geography_text=data.get("geography_text"),
            area_text=data.get("area_text"),
            ai_program_relevance=data.get("ai_program_relevance") or "UNKNOWN",
            value_creation_potential=data.get("value_creation_potential") or "UNKNOWN",
            comments=data.get("comments"),
        )
        db.add(event)
        db.flush()
        candidate.match_entity_type = ENTITY_EVENT
        candidate.match_entity_id = event.id
        self._commit_event_tags(db, event.id, data.get("tags") or [])
        self._audit(db, action="IMPORT_CREATE", entity_type=ENTITY_EVENT, entity_id=event.id, after_data=data)
        return event.id

    def _commit_event_participant(self, db: Session, candidate: ImportCandidate, entity_map: dict[str, UUID]) -> bool:
        event_candidate_id = candidate.candidate_data.get("event_candidate_id")
        event_id = entity_map.get(event_candidate_id)
        participant = candidate.candidate_data.get("participant") or {}
        if not event_id:
            return False
        db.add(
            EventParticipant(
                event_id=event_id,
                participant_role=participant.get("participant_role") or "ATTENDEE",
                participant_name=participant.get("participant_name"),
                participant_note=participant.get("participant_note"),
            )
        )
        return True

    def _commit_ai_tool(self, db: Session, candidate: ImportCandidate) -> bool:
        data = candidate.candidate_data.get("ai_tool") or {}
        if not data.get("name"):
            return False
        db.add(
            AITool(
                name=data["name"],
                category_text=data.get("category_text"),
                solution_summary=data.get("solution_summary"),
                notes=data.get("notes"),
            )
        )
        return True

    def _commit_note(self, db: Session, candidate: ImportCandidate, entity_map: dict[str, UUID]) -> bool:
        entity_candidate_id = candidate.candidate_data.get("entity_candidate_id")
        entity_id = entity_map.get(entity_candidate_id)
        note = candidate.candidate_data.get("note") or {}
        if not entity_id or not note.get("body"):
            return False
        db.add(
            Note(
                entity_type=candidate.candidate_data.get("entity_type") or "UNKNOWN",
                entity_id=entity_id,
                note_type=note.get("note_type") or "IMPORT_NOTE",
                body=note["body"],
                created_by_user_id=None,
            )
        )
        return True

    def _resolve_organization_id(self, db: Session, data: dict[str, Any], entity_map: dict[str, UUID]) -> UUID | None:
        organization_id = data.get("organization_id")
        if organization_id:
            return UUID(str(organization_id))
        candidate_id = data.get("organization_candidate_id")
        if candidate_id and candidate_id in entity_map:
            return entity_map[candidate_id]
        if candidate_id:
            candidate = db.get(ImportCandidate, UUID(str(candidate_id)))
            if candidate and candidate.match_entity_id:
                return candidate.match_entity_id
        return None

    def _commit_organization_tags(self, db: Session, organization_id: UUID, tags: list[dict[str, str]]) -> None:
        for tag_payload in tags:
            tag = self._get_or_create_tag(db, tag_payload["label"], tag_payload["tag_group"])
            existing = db.execute(
                select(OrganizationTag).where(
                    OrganizationTag.organization_id == organization_id,
                    OrganizationTag.tag_id == tag.id,
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(OrganizationTag(organization_id=organization_id, tag_id=tag.id, source="IMPORT"))

    def _commit_event_tags(self, db: Session, event_id: UUID, tags: list[dict[str, str]]) -> None:
        for tag_payload in tags:
            tag = self._get_or_create_tag(db, tag_payload["label"], tag_payload["tag_group"])
            existing = db.execute(
                select(EventTag).where(EventTag.event_id == event_id, EventTag.tag_id == tag.id)
            ).scalar_one_or_none()
            if not existing:
                db.add(EventTag(event_id=event_id, tag_id=tag.id, source="IMPORT"))

    def _get_or_create_tag(self, db: Session, label: str, tag_group: str) -> Tag:
        code = f"{tag_group}_{self._slug(label)}"[:120]
        tag = db.execute(select(Tag).where(Tag.code == code)).scalar_one_or_none()
        if tag:
            return tag
        tag = Tag(code=code, label=label, tag_group=tag_group)
        db.add(tag)
        db.flush()
        return tag

    def _category_code(self, category_tags: list[dict[str, str]]) -> str | None:
        if not category_tags:
            return None
        return f"CATEGORY_{self._slug(category_tags[0]['label'])}"[:120]

    def _serialize_candidate(self, candidate: ImportCandidate) -> dict[str, Any]:
        return {
            "id": str(candidate.id),
            "import_batch_id": str(candidate.import_batch_id),
            "import_row_id": str(candidate.import_row_id) if candidate.import_row_id else None,
            "entity_type": candidate.entity_type,
            "action_type": candidate.action_type,
            "match_entity_type": candidate.match_entity_type,
            "match_entity_id": str(candidate.match_entity_id) if candidate.match_entity_id else None,
            "candidate_data": candidate.candidate_data,
            "raw_source": candidate.raw_source,
            "validation_status": candidate.validation_status,
            "decision_status": candidate.decision_status,
            "decision_reason": candidate.decision_reason,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
        }

    def _duplicate_match_summary(self, candidates: list[ImportCandidate]) -> dict[str, Any]:
        return {
            "matched_existing": sum(1 for candidate in candidates if candidate.action_type == "MATCH"),
            "needs_review": sum(1 for candidate in candidates if candidate.action_type == "NEEDS_REVIEW"),
            "creates": sum(1 for candidate in candidates if candidate.action_type == "CREATE"),
        }

    def _candidate_warning_summary(self, candidates: list[ImportCandidate]) -> list[dict[str, Any]]:
        warnings = []
        for candidate in candidates:
            reason = candidate.candidate_data.get("reason")
            if reason:
                warnings.append(
                    {
                        "candidate_id": str(candidate.id),
                        "entity_type": candidate.entity_type,
                        "validation_status": candidate.validation_status,
                        "reason": reason,
                    }
                )
        return warnings[:100]

    def _can_commit(self, candidates: list[ImportCandidate], batch_status: str) -> bool:
        if batch_status == "COMMITTED" or not candidates:
            return False
        return not any(
            candidate.validation_status in {"ERROR", "NEEDS_REVIEW"} and candidate.decision_status == PENDING
            for candidate in candidates
        )

    def _contact_data(self, raw_text: str) -> dict[str, Any]:
        email = self._extract_email(raw_text)
        full_name = raw_text
        if email:
            full_name = raw_text.replace(email, "")
            full_name = re.sub(r"[<>()]", " ", full_name)
            full_name = " ".join(full_name.split()) or None
        elif "@" in raw_text:
            full_name = None
        return {"full_name": full_name, "email": email, "raw_contact_text": raw_text}

    def _status_code(self, value: Any, vocabulary: str) -> str | None:
        if value in (None, ""):
            return None
        normalized = self._normalize_key(str(value))
        for code, config in (self.status_mapping.get(vocabulary) or {}).items():
            values = [code, config.get("label"), *(config.get("aliases") or [])]
            if normalized in {self._normalize_key(str(item)) for item in values if item not in (None, "")}:
                return code
        return None

    def _status_id(self, db: Session, code: str | None, vocabulary: str) -> UUID | None:
        if not code:
            return None
        status_obj = db.execute(
            select(Status).where(Status.status_group == vocabulary.upper(), Status.code == code)
        ).scalar_one_or_none()
        return status_obj.id if status_obj else None

    def _borusan_fit_columns(self) -> dict[str, str]:
        columns = {}
        for code, payload in (self.borusan_mapping.get("borusan_companies") or {}).items():
            if code not in {"BORU", "BORCELIK", "SUPSAN", "OTO", "CAT", "ENERGY", "PORT"}:
                continue
            for column_name in payload.get("legacy_excel_columns") or []:
                columns[column_name] = code
        return columns

    def _borusan_company_code(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        normalized = self._normalize_key(str(value))
        for code, payload in (self.borusan_mapping.get("borusan_companies") or {}).items():
            values = [code, payload.get("name"), payload.get("english_name"), *(payload.get("aliases") or [])]
            if normalized in {self._normalize_key(str(item)) for item in values if item not in (None, "")}:
                return code if code != "BORUSAN_NEXT" else None
        return None

    def _borusan_company(self, db: Session, code: str | None) -> BorusanCompany | None:
        if not code:
            return None
        return db.execute(select(BorusanCompany).where(BorusanCompany.code == code)).scalar_one_or_none()

    def _split_tags(self, value: Any, tag_group: str) -> list[dict[str, str]]:
        if value in (None, ""):
            return []
        parts = re.split(r"[,;/|]", str(value))
        tags = []
        seen = set()
        for part in parts:
            label = " ".join(part.strip().split())
            if not label:
                continue
            key = self._normalize_key(label)
            if key in seen:
                continue
            seen.add(key)
            tags.append({"label": label, "tag_group": tag_group})
        return tags

    def _extract_domain(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        candidate = str(value).strip()
        if " " in candidate:
            return None
        if "://" not in candidate:
            candidate = f"https://{candidate}"
        parsed = urlparse(candidate)
        domain = (parsed.netloc or "").split("@")[-1].split(":")[0].lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if "." in domain else None

    def _extract_email(self, value: str) -> str | None:
        match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", value, re.IGNORECASE)
        return match.group(0).lower() if match else None

    def _is_truthy(self, value: Any) -> bool:
        if value in (None, ""):
            return False
        truthy = {
            self._normalize_key(str(item))
            for item in ((self.borusan_mapping.get("fit_values") or {}).get("truthy") or ["x", "yes", "true", "1"])
        }
        return self._normalize_key(str(value)) in truthy

    def _normalize_name(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        normalized = self._normalize_key(str(value))
        normalized = re.sub(r"[^\w\s.-]", "", normalized, flags=re.UNICODE)
        return " ".join(normalized.split())

    def _normalize_key(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value or "").casefold()
        return " ".join(normalized.strip().split())

    def _slug(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value.upper()).strip("_")
        return slug or "TAG"

    def _iso_date_or_none(self, value: Any) -> Any:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            return value
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None

    def _iso_date_string_or_none(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            return str(value)
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            return None

    def _event_geography(self, location: Any) -> str | None:
        if not location:
            return None
        parts = [part.strip() for part in str(location).split(",") if part.strip()]
        return parts[-1] if parts else str(location)

    def _audit(
        self,
        db: Session,
        *,
        action: str,
        entity_type: str,
        entity_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        after_data: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                after_data=after_data,
                created_at=datetime.now(timezone.utc),
            )
        )
