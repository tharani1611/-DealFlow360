import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, ForeignKey, text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.quotation import Quotation, QuotationItem
    from app.models.user import User
    from app.models.portal_user import PortalUser


class QuotationLineComment(Base, UUIDMixin):
    """Quotation line item comments for negotiation and discussion."""
    __tablename__ = "quotation_line_comments"

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
    quotation_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_type: Mapped[str] = mapped_column(String(20), nullable=False, default="INTERNAL_USER", server_default="INTERNAL_USER")
    author_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    author_portal_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portal_users.id", ondelete="SET NULL"),
        nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()")
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    quotation: Mapped["Quotation"] = relationship("Quotation")
    quotation_item: Mapped["QuotationItem"] = relationship("QuotationItem")
    author_user: Mapped[Optional["User"]] = relationship("User")
    author_portal_user: Mapped[Optional["PortalUser"]] = relationship("PortalUser")
