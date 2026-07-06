from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    audit_logs = relationship("AuditLog", back_populates="actor")


class UserSectionAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_section_access"
    __table_args__ = (
        UniqueConstraint("user_id", "section_key", name="uq_user_section_access_user_section"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    section_key: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    access_level: Mapped[str] = mapped_column(String(20), nullable=False, default="HIDDEN")
    granted_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)

    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
