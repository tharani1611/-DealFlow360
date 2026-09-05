from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer
    from app.models.contact import Contact
    from app.models.product import Product


class Organization(Base, UUIDMixin, TimestampMixin):
    """Organization model representing a tenant company using DealFlow360."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="organization")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="organization")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="organization")
