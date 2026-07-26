from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # Authentication is Microsoft Entra ID only. The application deliberately
    # stores no password or other local credential material: `email` holds the
    # Entra UPN and is the sole identity key.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    audit_logs = relationship("AuditLog", back_populates="actor")


class UserSectionAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-user, per-section access level.

    Keyed by the user's UPN (User Principal Name, as issued by Microsoft Entra
    ID) rather than the internal user id, so access can be granted before a
    user's first SSO sign-in and survives identity re-provisioning. In local
    auth mode the user's lower-cased email doubles as the UPN.
    """

    __tablename__ = "user_section_access"
    __table_args__ = (
        UniqueConstraint("user_upn", "section_key", name="uq_user_section_access_upn_section"),
    )

    user_upn: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    section_key: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    access_level: Mapped[str] = mapped_column(String(20), nullable=False, default="HIDDEN")
    granted_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)

    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
