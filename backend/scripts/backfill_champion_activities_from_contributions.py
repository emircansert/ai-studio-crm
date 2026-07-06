import asyncio
from typing import Any

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import UserContribution
from app.services.champion_score import write_champion_activity
from app.services.soft_delete import not_excluded

CONTRIBUTION_TO_CHAMPION: dict[str, dict[str, Any]] = {
    "ORGANIZATION_CREATED": {
        "category": "ECOSYSTEM_LIBRARY",
        "activity_type": "STARTUP_ADDED",
        "related_entity_type": "ORGANIZATION",
    },
    "CONTACT_CREATED": {
        "category": "ECOSYSTEM_LIBRARY",
        "activity_type": "CONTACT_ADDED",
        "related_entity_type": "CONTACT",
    },
    "OPPORTUNITY_CREATED": {
        "category": "VISION_STRATEGY",
        "activity_type": "OPPORTUNITY_CREATED",
        "related_entity_type": "OPPORTUNITY",
    },
    "EVENT_CREATED": {
        "category": "ECOSYSTEM_LIBRARY",
        "activity_type": "EVENT_ADDED",
        "related_entity_type": "EVENT",
    },
    "FOLLOW_UP_COMPLETED": {
        "category": "STARTUP_SCOUTING",
        "activity_type": "FOLLOW_UP_COMPLETED",
        "related_entity_type": "FOLLOW_UP",
    },
}


async def main() -> None:
    db = SessionLocal()
    created_or_existing = 0
    try:
        contributions = db.execute(
            select(UserContribution).where(
                UserContribution.source == "MANUAL",
                not_excluded(UserContribution.is_excluded),
                UserContribution.contribution_type.in_(CONTRIBUTION_TO_CHAMPION.keys()),
            )
        ).scalars().all()
        for contribution in contributions:
            mapping = CONTRIBUTION_TO_CHAMPION[contribution.contribution_type]
            activity = await write_champion_activity(
                db,
                user_id=contribution.user_id,
                category=mapping["category"],
                activity_type=mapping["activity_type"],
                related_entity_type=mapping["related_entity_type"],
                related_entity_id=contribution.entity_id,
                activity_date=contribution.occurred_at,
                source="AUTO_CRM",
                status="ACTIVE",
                notes="Backfilled from manual CRM Activity Points",
                created_by_user_id=contribution.user_id,
            )
            if activity is not None:
                created_or_existing += 1
        db.commit()
        print(f"Backfill complete. Processed {created_or_existing} contribution mappings.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
