import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Any, Dict, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.quotation import Quotation
    from app.models.user import User


class QuotationVersion(Base, UUIDMixin):
    """Historical versions and negotiation audit snapshots for quotations."""
    __tablename__ = "quotation_versions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    margin_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()")
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    quotation: Mapped["Quotation"] = relationship("Quotation")
    created_by_user: Mapped[Optional["User"]] = relationship("User")
