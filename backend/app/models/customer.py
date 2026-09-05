import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.contact import Contact


class Customer(Base, UUIDMixin, TimestampMixin):
    """Customer model representing a customer company belonging to an Organization."""
    __tablename__ = "customers"

    __table_args__ = (
        Index("ix_customers_organization_id_name", "organization_id", "name"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="customers")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="customer")
