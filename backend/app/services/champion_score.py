from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.models import ChampionActivity, User, UserContribution
from app.services.soft_delete import not_archived, not_excluded

PERIODS = {
    "all_time": None,
    "last_30_days": timedelta(days=30),
    "last_7_days": timedelta(days=7),
}

CHAMPION_RULES: list[dict[str, Any]] = [
    {
        "category": "VISION_STRATEGY",
        "label": "Use Case & Project Development",
        "helper_label": "Use-case Önerisi ve Projelendirme",
        "weight": 40,
        "task": "Support business units in identifying AI development areas, sharing global use-case examples, and helping projectize ideas.",
        "kpi": "Department use-case recommendation and projectization.",
        "tracking_owner": "YZ Dönüşüm Ofisi",
        "qualifying_activity_types": ["OPPORTUNITY_CREATED", "USE_CASE_PROPOSED", "USE_CASE_PROJECTIZED", "OPPORTUNITY_MOVED_TO_PROJECT"],
        "thresholds": "0 project = 0; 1 project = 50; 2+ projects = 100",
    },
    {
        "category": "ECOSYSTEM_LIBRARY",
        "label": "Ecosystem Library Contribution",
        "weight": 15,
        "task": "Discover new technology vendors, startups, tools, products, and events; improve Ecosystem Library.",
        "kpi": "Pre-evaluated vendor/product/tool/startup/event recommendation.",
        "tracking_owner": "YZ Dönüşüm Ofisi",
        "qualifying_activity_types": [
            "STARTUP_ADDED",
            "VENDOR_ADDED",
            "AI_TOOL_ADDED",
            "EVENT_ADDED",
            "CONTACT_ADDED",
            "DECK_UPLOADED",
            "ORGANIZATION_ENRICHED",
        ],
        "thresholds": "0 contribution = 0; 1-7 contributions = 50; 8+ contributions = 100",
        "note": "Qualifying CRM actions such as adding startups, events, AI tools, contacts, and startup decks are counted here.",
    },
    {
        "category": "STARTUP_SCOUTING",
        "label": "Startup Scouting & AI Studio Support",
        "weight": 15,
        "task": "Actively support startup-related AI Studio work.",
        "kpi": "Startup scouting/review actions.",
        "tracking_owner": "YZ Dönüşüm Ofisi",
        "qualifying_activity_types": ["STARTUP_REVIEWED", "STARTUP_SHORTLISTED", "FOLLOW_UP_COMPLETED"],
        "thresholds": "0 scouting = 0; 1-4 scouting = 50; 5+ scouting = 100",
    },
    {
        "category": "COMMUNICATION_CASE_STUDY",
        "label": "Case Study Contribution",
        "weight": 10,
        "task": "Contribute to company success/learning stories as case studies.",
        "kpi": "Case study content contribution.",
        "tracking_owner": "YZ Dönüşüm Ofisi",
        "qualifying_activity_types": ["CASE_STUDY_SUBMITTED", "CASE_STUDY_APPROVED"],
        "thresholds": "0 case study = 0; 1 case study = 50; 2+ case studies = 100",
    },
    {
        "category": "COMMUNICATION_EVENT",
        "label": "Events & Communication Participation",
        "weight": 10,
        "task": "Take roles in AI Transformation Office communication events.",
        "kpi": "Event participation/support.",
        "tracking_owner": "YZ Dönüşüm Ofisi",
        "qualifying_activity_types": ["EVENT_PARTICIPATION"],
        "thresholds": "0-1 event = 0; 2-4 events = 50; 5+ events = 100",
    },
    {
        "category": "TRAINING",
        "label": "Training Completion",
        "weight": 10,
        "task": "Participate in Borusan Academy AI training programs.",
        "kpi": "Complete required internal AI training programs.",
        "tracking_owner": "Akademi",
        "qualifying_activity_types": ["TRAINING_COMPLETED"],
        "thresholds": "Incomplete/missing = 0; complete = 100",
    },
]

RULE_BY_CATEGORY = {rule["category"]: rule for rule in CHAMPION_RULES}
QUALIFYING_ACTIVITY_TYPES = {rule["category"]: set(rule["qualifying_activity_types"]) for rule in CHAMPION_RULES}
COUNTED_SOURCES = {"AUTO_CRM", "ADMIN_RECORDED", "CSV_IMPORT"}
COUNTED_STATUSES = {"ACTIVE", "APPROVED"}


def period_start(period: str) -> datetime | None:
    delta = PERIODS.get(period)
    if delta is None:
        return None
    return datetime.now(timezone.utc) - delta


def category_score(category: str, count: int) -> int:
    if category == "VISION_STRATEGY":
        return 0 if count == 0 else 50 if count == 1 else 100
    if category == "ECOSYSTEM_LIBRARY":
        return 0 if count == 0 else 50 if count <= 7 else 100
    if category == "STARTUP_SCOUTING":
        return 0 if count == 0 else 50 if count <= 4 else 100
    if category == "COMMUNICATION_CASE_STUDY":
        return 0 if count == 0 else 50 if count == 1 else 100
    if category == "COMMUNICATION_EVENT":
        return 0 if count <= 1 else 50 if count <= 4 else 100
    if category == "TRAINING":
        return 100 if count >= 1 else 0
    return 0


def next_action_hint(category: str, count: int) -> str | None:
    if category == "VISION_STRATEGY":
        if count == 0:
            return "Add 1 use case or opportunity to reach 50."
        if count == 1:
            return "Add 1 more use case or opportunity to reach 100."
    if category == "ECOSYSTEM_LIBRARY":
        if count == 0:
            return "Add 1 ecosystem contribution to reach 50."
        if count <= 7:
            return f"Add {8 - count} more ecosystem contributions to reach 100."
    if category == "STARTUP_SCOUTING":
        if count == 0:
            return "Complete 1 scouting/review action to reach 50."
        if count <= 4:
            return f"Complete {5 - count} more scouting/review actions to reach 100."
    if category == "COMMUNICATION_CASE_STUDY":
        if count == 0:
            return "Record 1 case study contribution to reach 50."
        if count == 1:
            return "Record 1 more case study contribution to reach 100."
    if category == "COMMUNICATION_EVENT":
        if count <= 1:
            return f"Record {2 - count} more event participation activities to reach 50."
        if count <= 4:
            return f"Record {5 - count} more event participation activities to reach 100."
    if category == "TRAINING" and count == 0:
        return "Record completed Borusan Academy AI training to reach 100."
    return None


async def write_champion_activity(
    db: Session,
    *,
    user_id: UUID | None,
    category: str,
    activity_type: str,
    related_entity_type: str | None = None,
    related_entity_id: UUID | None = None,
    activity_date: datetime | None = None,
    quantity: int = 1,
    source: str = "AUTO_CRM",
    status: str = "ACTIVE",
    evidence_url: str | None = None,
    notes: str | None = None,
    created_by_user_id: UUID | None = None,
    commit: bool = False,
) -> ChampionActivity | None:
    if user_id is None:
        return None
    if source == "AUTO_CRM" and related_entity_type and related_entity_id:
        existing = db.execute(
            select(ChampionActivity).where(
                ChampionActivity.user_id == user_id,
                ChampionActivity.category == category,
                ChampionActivity.activity_type == activity_type,
                ChampionActivity.related_entity_type == related_entity_type,
                ChampionActivity.related_entity_id == related_entity_id,
                ChampionActivity.source == source,
                not_archived(ChampionActivity.is_archived),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    now = datetime.now(timezone.utc)
    activity = ChampionActivity(
        user_id=user_id,
        category=category,
        activity_type=activity_type,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        activity_date=activity_date or now,
        quantity=max(quantity or 1, 1),
        source=source,
        status=status,
        evidence_url=evidence_url,
        notes=notes,
        created_by_user_id=created_by_user_id,
    )
    db.add(activity)
    if commit:
        db.commit()
        db.refresh(activity)
    return activity


def _activity_stmt(period: str, user_id: UUID | None = None) -> Any:
    stmt = select(ChampionActivity).where(
        not_archived(ChampionActivity.is_archived),
        ChampionActivity.source.in_(COUNTED_SOURCES),
        ChampionActivity.status.in_(COUNTED_STATUSES),
    )
    start = period_start(period)
    if start:
        stmt = stmt.where(ChampionActivity.activity_date >= start)
    if user_id:
        stmt = stmt.where(ChampionActivity.user_id == user_id)
    return stmt.order_by(ChampionActivity.activity_date.desc(), ChampionActivity.id.desc())


def _crm_contributions_by_user(db: Session, period: str) -> dict[UUID, dict[str, Any]]:
    stmt = select(UserContribution).where(UserContribution.source == "MANUAL", not_excluded(UserContribution.is_excluded))
    start = period_start(period)
    if start:
        stmt = stmt.where(UserContribution.occurred_at >= start)
    rows = db.execute(stmt.order_by(UserContribution.occurred_at.desc(), UserContribution.id.desc())).scalars().all()
    summary: dict[UUID, dict[str, Any]] = defaultdict(lambda: {"points": 0, "recent": [], "counts": defaultdict(int)})
    for contribution in rows:
        item = summary[contribution.user_id]
        item["points"] += contribution.points or 0
        item["counts"][contribution.contribution_type] += 1
        if len(item["recent"]) < 5:
            item["recent"].append(
                {
                    "contribution_type": contribution.contribution_type,
                    "entity_type": contribution.entity_type,
                    "entity_id": contribution.entity_id,
                    "points": contribution.points,
                    "occurred_at": contribution.occurred_at,
                }
            )
    for item in summary.values():
        item["counts"] = dict(item["counts"])
    return summary


def _score_row(
    user: User,
    activities: list[ChampionActivity],
    crm_contribution_summary: dict[str, Any] | None = None,
    rank: int | None = None,
) -> dict[str, Any]:
    crm_summary = crm_contribution_summary or {"points": 0, "recent": [], "counts": {}}
    raw_counts = {rule["category"]: 0 for rule in CHAMPION_RULES}
    activity_type_counts: dict[str, int] = defaultdict(int)
    last_activity_at: datetime | None = None

    for activity in activities:
        if activity.activity_type not in QUALIFYING_ACTIVITY_TYPES.get(activity.category, set()):
            continue
        quantity = max(activity.quantity or 1, 1)
        raw_counts[activity.category] = raw_counts.get(activity.category, 0) + quantity
        activity_type_counts[activity.activity_type] += quantity
        if last_activity_at is None or activity.activity_date > last_activity_at:
            last_activity_at = activity.activity_date

    weighted_breakdown: dict[str, dict[str, Any]] = {}
    champion_score = 0.0
    missing_targets: list[str] = []
    for rule in CHAMPION_RULES:
        category = rule["category"]
        count = raw_counts.get(category, 0)
        score = category_score(category, count)
        weighted = score * (rule["weight"] / 100)
        champion_score += weighted
        hint = next_action_hint(category, count)
        if hint:
            missing_targets.append(hint)
        weighted_breakdown[category] = {
            "label": rule["label"],
            "helper_label": rule.get("helper_label"),
            "weight": rule["weight"],
            "raw_count": count,
            "category_score": score,
            "weighted_score": round(weighted, 1),
        }

    def score_for(category: str) -> int:
        return int(weighted_breakdown[category]["category_score"])

    return {
        "rank": rank,
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "champion_score": round(champion_score, 1),
        "crm_activity_points": crm_summary.get("points", 0),
        "crm_activity_points_role": "internal_operational_evidence",
        "crm_activity_breakdown": crm_summary.get("counts", {}),
        "recent_crm_activity_evidence": crm_summary.get("recent", []),
        "vision_strategy_score": score_for("VISION_STRATEGY"),
        "ecosystem_library_score": score_for("ECOSYSTEM_LIBRARY"),
        "ecosystem_library_raw_count": raw_counts.get("ECOSYSTEM_LIBRARY", 0),
        "startup_scouting_score": score_for("STARTUP_SCOUTING"),
        "case_study_score": score_for("COMMUNICATION_CASE_STUDY"),
        "event_participation_score": score_for("COMMUNICATION_EVENT"),
        "training_score": score_for("TRAINING"),
        "weighted_breakdown": weighted_breakdown,
        "raw_counts": raw_counts,
        "activity_type_counts": dict(activity_type_counts),
        "last_activity_at": last_activity_at,
        "missing_targets": missing_targets,
    }


def champion_leaderboard(db: Session, *, period: str = "all_time", limit: int = 50) -> dict[str, Any]:
    activities = db.execute(_activity_stmt(period)).scalars().all()
    activities_by_user: dict[UUID, list[ChampionActivity]] = defaultdict(list)
    for activity in activities:
        activities_by_user[activity.user_id].append(activity)

    crm_contributions = _crm_contributions_by_user(db, period)
    user_ids = set(activities_by_user.keys()) | set(crm_contributions.keys())
    users = []
    if user_ids:
        users = db.execute(select(User).where(User.id.in_(user_ids), User.is_active == true())).scalars().all()

    rows = [_score_row(user, activities_by_user.get(user.id, []), crm_contributions.get(user.id)) for user in users]
    rows.sort(key=lambda row: (row["champion_score"], _timestamp(row["last_activity_at"])), reverse=True)

    previous_key: tuple[Any, ...] | None = None
    rank = 0
    for index, row in enumerate(rows, start=1):
        current_key = (row["champion_score"],)
        if current_key != previous_key:
            rank = index
            previous_key = current_key
        row["rank"] = rank

    return {
        "period": period,
        "items": rows[:limit],
        "total_users": len(rows),
        "scorecard": CHAMPION_RULES,
    }


def champion_user_position(db: Session, *, user: User, period: str = "all_time") -> dict[str, Any]:
    rows = champion_leaderboard(db, period=period, limit=1000)["items"]
    for row in rows:
        if row["user_id"] == user.id:
            return {"period": period, **row}
    return {"period": period, **_score_row(user, [], _crm_contributions_by_user(db, period).get(user.id), rank=None)}


def champion_user_detail(db: Session, *, user_id: UUID, period: str = "all_time") -> dict[str, Any] | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    score = champion_user_position(db, user=user, period=period)
    activities = db.execute(_activity_stmt(period, user_id=user_id)).scalars().all()
    score["activities"] = [
        {
            "id": activity.id,
            "category": activity.category,
            "activity_type": activity.activity_type,
            "related_entity_type": activity.related_entity_type,
            "related_entity_id": activity.related_entity_id,
            "activity_date": activity.activity_date,
            "quantity": activity.quantity,
            "source": activity.source,
            "status": activity.status,
            "evidence_url": activity.evidence_url,
            "notes": activity.notes,
        }
        for activity in activities
    ]
    return score


def _timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    return value.timestamp()
