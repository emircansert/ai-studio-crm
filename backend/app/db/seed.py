import os
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import BorusanCompany, Status, User


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml(filename: str) -> dict[str, Any]:
    with (CONFIG_DIR / filename).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def upsert_statuses() -> None:
    status_config = load_yaml("status_mapping.yml")
    order = 0
    with SessionLocal() as db:
        for group_name, statuses in status_config.items():
            if group_name == "version":
                continue
            status_group = group_name.upper()
            for code, payload in statuses.items():
                order += 10
                is_terminal = code in {
                    "POC_FAILED",
                    "NOT_A_FIT",
                    "NOT_CONTINUING",
                    "NO_CLOSE_RELATIONSHIP",
                }
                result = db.execute(
                    select(Status).where(
                        Status.status_group == status_group,
                        Status.code == code,
                    )
                )
                status = result.scalar_one_or_none()
                if status is None:
                    db.add(
                        Status(
                            code=code,
                            label=payload["label"],
                            status_group=status_group,
                            sort_order=order,
                            is_terminal=is_terminal,
                        )
                    )
                else:
                    status.label = payload["label"]
                    status.status_group = status_group
                    status.sort_order = order
                    status.is_terminal = is_terminal
        db.commit()


def upsert_borusan_companies() -> None:
    company_config = load_yaml("borusan_company_mapping.yml")["borusan_companies"]
    allowed_codes = {"BORU", "BORCELIK", "SUPSAN", "OTO", "CAT", "ENERGY", "PORT"}
    with SessionLocal() as db:
        for code, payload in company_config.items():
            if code not in allowed_codes:
                continue
            result = db.execute(select(BorusanCompany).where(BorusanCompany.code == code))
            company = result.scalar_one_or_none()
            legacy_columns = payload.get("legacy_excel_columns") or []
            values = {
                "name": payload["name"],
                "english_name": payload.get("english_name"),
                "legacy_excel_column": legacy_columns[0] if legacy_columns else None,
                "aliases": payload.get("aliases"),
                "is_active": True,
            }
            if company is None:
                db.add(BorusanCompany(code=code, **values))
            else:
                for field_name, value in values.items():
                    setattr(company, field_name, value)
        db.commit()


def create_initial_admin() -> None:
    """Pre-provision an ADMIN row so an administrator exists before first sign-in.

    No credential is created: authentication is Microsoft Entra ID only. The
    email must match the administrator's Entra UPN for the account to be
    matched at sign-in.
    """
    email = os.getenv("INITIAL_ADMIN_EMAIL")
    full_name = os.getenv("INITIAL_ADMIN_FULL_NAME", "Initial Admin")
    if not email:
        return
    with SessionLocal() as db:
        result = db.execute(select(User).where(User.email == email.lower()))
        if result.scalar_one_or_none() is not None:
            return
        db.add(
            User(
                email=email.lower(),
                full_name=full_name,
                role="ADMIN",
                is_active=True,
            )
        )
        db.commit()


def main() -> None:
    upsert_statuses()
    upsert_borusan_companies()
    create_initial_admin()


if __name__ == "__main__":
    main()
