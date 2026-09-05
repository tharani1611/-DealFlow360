import uuid
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import String, Numeric, ForeignKey, Date, DateTime, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.customer import Customer
    from app.models.invoice import Invoice
    from app.models.user import User


class Payment(Base, UUIDMixin, TimestampMixin):
    """Payment model recording financial transaction against an invoice."""
    __tablename__ = "payments"

    __table_args__ = (
        UniqueConstraint("organization_id", "payment_reference", name="uq_payments_org_payment_ref"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_reference: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="BANK_TRANSFER",
        server_default=text("'BANK_TRANSFER'"),
    )  # BANK_TRANSFER, CARD, CASH, CHEQUE, UPI, OTHER
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="COMPLETED",
        server_default=text("'COMPLETED'"),
        index=True,
    )  # COMPLETED, VOID
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    customer: Mapped["Customer"] = relationship("Customer")
    invoice: Mapped["Invoice"] = relationship("Invoice")
    created_by_user: Mapped[Optional["User"]] = relationship("User")
