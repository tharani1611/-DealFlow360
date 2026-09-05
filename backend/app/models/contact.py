import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.customer import Customer


class Contact(Base, UUIDMixin, TimestampMixin):
    """Contact model representing an individual contact person for a Customer."""
    __tablename__ = "contacts"

    __table_args__ = (
        Index("ix_contacts_organization_id_customer_id", "organization_id", "customer_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="contacts")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")
