from typing import Any

from sqlalchemy import false, or_, true


def not_archived(column: Any) -> Any:
    return or_(column == false(), column.is_(None))


def archived(column: Any) -> Any:
    return column == true()


def not_excluded(column: Any) -> Any:
    return or_(column == false(), column.is_(None))
