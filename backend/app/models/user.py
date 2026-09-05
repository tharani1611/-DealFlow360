import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class User(Base, UUIDMixin, TimestampMixin):
    """User model representing an application user belonging to an Organization."""
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_organization_id_email"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")

    @property
    def role(self) -> str:
        """Returns effective role name derived from is_admin."""
        return "admin" if self.is_admin else "user"
