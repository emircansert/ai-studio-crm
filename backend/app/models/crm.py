import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import ArchiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Status(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statuses"
    __table_args__ = (
        UniqueConstraint("status_group", "code", name="uq_statuses_status_group_code"),
    )

    code: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    status_group: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Organization(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    organization_subtype: Mapped[str | None] = mapped_column(String(80), index=True)
    category_code: Mapped[str | None] = mapped_column(String(120), index=True)
    category_label: Mapped[str | None] = mapped_column(String(255), index=True)
    vertical_text: Mapped[str | None] = mapped_column(String(255), index=True)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    website_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    geography_text: Mapped[str | None] = mapped_column(String(255), index=True)
    country_codes: Mapped[list[str] | None] = mapped_column(JSON)
    source_text: Mapped[str | None] = mapped_column(String(512), index=True)
    added_by_text: Mapped[str | None] = mapped_column(String(255))
    solution_summary: Mapped[str | None] = mapped_column(Text)
    lifecycle_status_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("statuses.id"),
    )
    relationship_status_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("statuses.id"),
    )
    last_contact_date: Mapped[date | None] = mapped_column(Date)
    raw_import_ref: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_rows.id"),
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_tags: Mapped[list[str] | None] = mapped_column(JSON)

    lifecycle_status = relationship("Status", foreign_keys=[lifecycle_status_id])
    relationship_status = relationship("Status", foreign_keys=[relationship_status_id])
    contacts = relationship("Contact", back_populates="organization", cascade="all, delete-orphan")
    borusan_fits = relationship(
        "OrganizationBorusanFit",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    tags = relationship("OrganizationTag", back_populates="organization", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="organization")
    documents = relationship("OrganizationDocument", back_populates="organization")


Index("ix_organizations_type_status", Organization.organization_type, Organization.lifecycle_status_id)
Index("ix_organizations_type_geography", Organization.organization_type, Organization.geography_text)
Index("ix_organizations_type_source", Organization.organization_type, Organization.source_text)


class Contact(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "contacts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(80))
    title: Mapped[str | None] = mapped_column(String(255))
    contact_source: Mapped[str] = mapped_column(String(80), nullable=False, default="MANUAL")
    raw_contact_text: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )

    organization = relationship("Organization", back_populates="contacts")


class OrganizationStatusHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "organization_status_history"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("statuses.id"),
        nullable=False,
    )
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class BorusanCompany(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "borusan_companies"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[str | None] = mapped_column(String(255))
    legacy_excel_column: Mapped[str | None] = mapped_column(String(120))
    aliases: Mapped[list[str] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization_fits = relationship("OrganizationBorusanFit", back_populates="borusan_company")
    opportunities = relationship("Opportunity", back_populates="borusan_company")


class OrganizationBorusanFit(UUIDPrimaryKeyMixin, ArchiveMixin, Base):
    __tablename__ = "organization_borusan_fit"
    __table_args__ = (
        UniqueConstraint("organization_id", "borusan_company_id", name="uq_org_borusan_fit"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    borusan_company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("borusan_companies.id"),
        nullable=False,
    )
    fit_level: Mapped[str] = mapped_column(String(32), nullable=False, default="RELEVANT")
    fit_reason: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="MANUAL")
    raw_value: Mapped[str | None] = mapped_column(String(255))

    organization = relationship("Organization", back_populates="borusan_fits")
    borusan_company = relationship("BorusanCompany", back_populates="organization_fits")


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tags"

    code: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    tag_group: Mapped[str] = mapped_column(String(80), index=True, nullable=False)

    organizations = relationship("OrganizationTag", back_populates="tag")
    events = relationship("EventTag", back_populates="tag")


class OrganizationTag(Base):
    __tablename__ = "organization_tags"
    __table_args__ = (UniqueConstraint("organization_id", "tag_id", name="uq_organization_tag"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tags.id"),
        primary_key=True,
    )
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="MANUAL")
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))

    organization = relationship("Organization", back_populates="tags")
    tag = relationship("Tag", back_populates="organizations")


class Opportunity(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "opportunities"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
        index=True,
        nullable=False,
    )
    borusan_company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("borusan_companies.id"),
        index=True,
        nullable=False,
    )
    opportunity_type: Mapped[str] = mapped_column(String(80), nullable=False, default="POC")
    stage: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    stage_migration_note: Mapped[str | None] = mapped_column(Text)
    status_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("statuses.id"),
    )
    topic: Mapped[str | None] = mapped_column(Text)
    terms_text: Mapped[str | None] = mapped_column(Text)
    value_hypothesis: Mapped[str | None] = mapped_column(Text)
    expected_start_date: Mapped[date | None] = mapped_column(Date)
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    last_contact_date: Mapped[date | None] = mapped_column(Date)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    next_action_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))

    organization = relationship("Organization", back_populates="opportunities")
    borusan_company = relationship("BorusanCompany", back_populates="opportunities")
    status = relationship("Status")
    documents = relationship("OpportunityDocument", back_populates="opportunity")


class UseCaseProposal(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "use_case_proposals"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    borusan_company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("borusan_companies.id"),
        index=True,
    )
    business_unit_text: Mapped[str | None] = mapped_column(String(255), index=True)
    proposer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    related_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
        index=True,
    )
    problem_area: Mapped[str | None] = mapped_column(Text)
    proposed_solution: Mapped[str | None] = mapped_column(Text)
    expected_impact: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="IDEA")
    stage: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="IDEA")
    priority: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="MEDIUM")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )


class Event(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "events"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    date_text: Mapped[str | None] = mapped_column(String(255))
    location_text: Mapped[str] = mapped_column(String(255), nullable=False)
    geography_text: Mapped[str | None] = mapped_column(String(255), index=True)
    area_text: Mapped[str | None] = mapped_column(String(255))
    ai_program_relevance: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    value_creation_potential: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    comments: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )

    tags = relationship("EventTag", back_populates="event", cascade="all, delete-orphan")
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")


class EventTag(Base):
    __tablename__ = "event_tags"
    __table_args__ = (UniqueConstraint("event_id", "tag_id", name="uq_event_tag"),)

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tags.id"),
        primary_key=True,
    )
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="MANUAL")

    event = relationship("Event", back_populates="tags")
    tag = relationship("Tag", back_populates="events")


class EventParticipant(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "event_participants"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    participant_role: Mapped[str] = mapped_column(String(120), nullable=False)
    participant_name: Mapped[str | None] = mapped_column(String(255))
    participant_note: Mapped[str | None] = mapped_column(Text)

    event = relationship("Event", back_populates="participants")


class ProgramActivity(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "program_activities"

    activity_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    activity_date: Mapped[date | None] = mapped_column(Date, index=True)
    location_text: Mapped[str | None] = mapped_column(String(255))
    owner_team: Mapped[str | None] = mapped_column(String(255))
    tracking_owner: Mapped[str | None] = mapped_column(String(255))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )

    participants = relationship("ProgramActivityParticipant", back_populates="program_activity", cascade="all, delete-orphan")


class ProgramActivityParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "program_activity_participants"

    program_activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("program_activities.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    role: Mapped[str | None] = mapped_column(String(80), index=True)
    attendance_status: Mapped[str | None] = mapped_column(String(40), index=True)
    completion_status: Mapped[str | None] = mapped_column(String(40), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )

    program_activity = relationship("ProgramActivity", back_populates="participants")


class AITool(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "ai_tools"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), index=True)
    vendor_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
    )
    website_url: Mapped[str | None] = mapped_column(String(1024))
    category_text: Mapped[str | None] = mapped_column(String(255), index=True)
    primary_use_case: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    solution_summary: Mapped[str | None] = mapped_column(Text)
    pricing_model: Mapped[str | None] = mapped_column(String(80), index=True)
    deployment_type: Mapped[str | None] = mapped_column(String(80), index=True)
    data_sensitivity_level: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="Identified", index=True)
    owner_notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(120), default="MANUAL", index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    added_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )


class Note(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "notes"

    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    note_type: Mapped[str] = mapped_column(String(80), nullable=False, default="GENERAL")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )


Index("ix_notes_entity", Note.entity_type, Note.entity_id)


class FollowUpAction(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "follow_up_actions"

    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index("ix_follow_up_actions_entity", FollowUpAction.entity_type, FollowUpAction.entity_id)


class ImportBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_batches"

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )
    status: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="UPLOADED")
    workbook_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    sheets = relationship("ImportSheet", back_populates="import_batch", cascade="all, delete-orphan")
    warnings = relationship("ImportWarning", back_populates="import_batch")
    candidates = relationship("ImportCandidate", cascade="all, delete-orphan")


class ImportSheet(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "import_sheets"

    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sheet_name: Mapped[str] = mapped_column(String(255), nullable=False)
    detected_entity: Mapped[str | None] = mapped_column(String(120))
    header_row: Mapped[int | None] = mapped_column(Integer)
    row_count: Mapped[int | None] = mapped_column(Integer)
    column_mapping: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    import_batch = relationship("ImportBatch", back_populates="sheets")
    rows = relationship("ImportRow", back_populates="import_sheet", cascade="all, delete-orphan")


class ImportRow(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "import_rows"

    import_sheet_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_sheets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    excel_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    cleaned_values: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    normalized_candidate: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    row_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    validation_status: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="VALID")

    import_sheet = relationship("ImportSheet", back_populates="rows")
    warnings = relationship("ImportWarning", back_populates="import_row", cascade="all, delete-orphan")
    candidates = relationship("ImportCandidate", back_populates="import_row")


class ImportCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_candidates"

    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    import_row_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_rows.id"),
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    match_entity_type: Mapped[str | None] = mapped_column(String(80))
    match_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    candidate_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    raw_source: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    decision_status: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="PENDING")
    decision_reason: Mapped[str | None] = mapped_column(Text)

    import_row = relationship("ImportRow", back_populates="candidates")


class ImportWarning(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "import_warnings"

    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_batches.id"),
        index=True,
    )
    import_row_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_rows.id", ondelete="CASCADE"),
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(120))
    raw_value: Mapped[str | None] = mapped_column(Text)

    import_batch = relationship("ImportBatch", back_populates="warnings")
    import_row = relationship("ImportRow", back_populates="warnings")


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    actor = relationship("User", back_populates="audit_logs")


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String(80), index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_notifications_user_read_created", Notification.user_id, Notification.is_read, Notification.created_at)


class CrmActivityEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "crm_activity_events"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


Index("ix_crm_activity_events_created", CrmActivityEvent.created_at, CrmActivityEvent.id)
Index("ix_crm_activity_events_actor_created", CrmActivityEvent.actor_user_id, CrmActivityEvent.created_at)


class UserContribution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_contributions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    contribution_type: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="MANUAL")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    excluded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    exclusion_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_user_contributions_user_source_time", UserContribution.user_id, UserContribution.source, UserContribution.occurred_at)
Index("ix_user_contributions_type_source_time", UserContribution.contribution_type, UserContribution.source, UserContribution.occurred_at)


class ChampionActivity(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "champion_activities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(80), index=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    activity_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="AUTO_CRM")
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="ACTIVE")
    evidence_url: Mapped[str | None] = mapped_column(String(1024))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )


Index("ix_champion_activities_user_category_date", ChampionActivity.user_id, ChampionActivity.category, ChampionActivity.activity_date)
Index("ix_champion_activities_type_source_date", ChampionActivity.activity_type, ChampionActivity.source, ChampionActivity.activity_date)
Index(
    "ix_champion_activities_related",
    ChampionActivity.related_entity_type,
    ChampionActivity.related_entity_id,
)


class BrandingAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "branding_assets"

    asset_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OrganizationDocument(UUIDPrimaryKeyMixin, ArchiveMixin, Base):
    __tablename__ = "organization_documents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
        index=True,
        nullable=False,
    )
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="STARTUP_DECK")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(160), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organization = relationship("Organization", back_populates="documents")


class OpportunityDocument(UUIDPrimaryKeyMixin, ArchiveMixin, Base):
    __tablename__ = "opportunity_documents"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("opportunities.id"),
        index=True,
        nullable=False,
    )
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="POC_DOCUMENT")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(160), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    opportunity = relationship("Opportunity", back_populates="documents")


class Vendor(UUIDPrimaryKeyMixin, ArchiveMixin, TimestampMixin, Base):
    __tablename__ = "vendors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category_text: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    contact_info: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="PROSPECT", index=True)
    geography_text: Mapped[str | None] = mapped_column(String(255), index=True)
    last_contact_date: Mapped[date | None] = mapped_column(Date)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )

    ratings = relationship("VendorRating", back_populates="vendor", cascade="all, delete-orphan")


class VendorRating(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vendor_ratings"
    __table_args__ = (
        UniqueConstraint("vendor_id", "rater_user_id", name="uq_vendor_rating_vendor_rater"),
    )

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    rater_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reliability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    pricing_score: Mapped[int] = mapped_column(Integer, nullable=False)
    borusan_fit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    vendor = relationship("Vendor", back_populates="ratings")
    rater = relationship("User", foreign_keys=[rater_user_id])
