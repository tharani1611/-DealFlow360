import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Numeric, Text, ForeignKey, text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.quotation import Quotation, QuotationItem
    from app.models.portal_user import PortalUser
    from app.models.user import User


class QuotationChangeRequest(Base, UUIDMixin, TimestampMixin):
    """Customer change requests and counter-discount proposals."""
    __tablename__ = "quotation_change_requests"

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
    quotation_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="SET NULL"),
        nullable=True
    )
    requested_by_portal_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portal_users.id", ondelete="RESTRICT"),
        nullable=False
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN", server_default="OPEN")
    requested_discount_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    requested_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    request_details: Mapped[str] = mapped_column(Text, nullable=False)
    response_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    quotation: Mapped["Quotation"] = relationship("Quotation")
    quotation_item: Mapped[Optional["QuotationItem"]] = relationship("QuotationItem")
    requested_by_portal_user: Mapped["PortalUser"] = relationship("PortalUser")
    reviewed_by_user: Mapped[Optional["User"]] = relationship("User")
