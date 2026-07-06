from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Organization, OrganizationTag, Tag


def main() -> None:
    updated = 0
    with SessionLocal() as db:
        organizations = db.execute(select(Organization).order_by(Organization.name.asc())).scalars().all()
        for organization in organizations:
            tag_rows = db.execute(
                select(Tag)
                .join(OrganizationTag, OrganizationTag.tag_id == Tag.id)
                .where(OrganizationTag.organization_id == organization.id)
                .order_by(Tag.tag_group.asc(), Tag.label.asc())
            ).scalars().all()
            category = next((tag for tag in tag_rows if tag.tag_group == "CATEGORY"), None)
            verticals = [tag.label for tag in tag_rows if tag.tag_group == "VERTICAL"]
            changed = False
            if category and not organization.category_label:
                organization.category_code = category.code
                organization.category_label = category.label
                changed = True
            if verticals and not organization.vertical_text:
                organization.vertical_text = ", ".join(verticals)
                changed = True
            if changed:
                db.add(organization)
                updated += 1
        db.commit()
    print(f"Backfilled category/vertical for {updated} organizations.")


if __name__ == "__main__":
    main()
