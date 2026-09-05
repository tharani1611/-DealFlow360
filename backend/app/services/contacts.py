import uuid
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.contact import Contact
from app.models.customer import Customer
from app.schemas.contact import ContactCreate, ContactUpdate
from app.core.exceptions import NotFoundException

logger = logging.getLogger("dealflow360.contacts_service")


async def verify_customer_in_tenant(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID
) -> Customer:
    """Verifies target customer exists within the authenticated tenant context."""
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Target customer requested was not found")
    return customer


async def create_contact(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: ContactCreate
) -> Contact:
    """Creates a new Contact person linked to a Customer within the tenant."""
    # Critical tenant security verification: Ensure target customer belongs to the user's tenant
    await verify_customer_in_tenant(db, organization_id, payload.customer_id)

    contact = Contact(
        organization_id=organization_id,
        customer_id=payload.customer_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        job_title=payload.job_title,
        is_primary=payload.is_primary
    )
    db.add(contact)
    await db.flush()
    return contact


async def list_contacts(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None
) -> List[Contact]:
    """Retrieves contacts scoped strictly to the specified organization."""
    stmt = select(Contact).where(Contact.organization_id == organization_id)
    if customer_id is not None:
        # Validate customer belongs to tenant if specified
        stmt = stmt.where(Contact.customer_id == customer_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Contact.first_name.ilike(search_pattern),
                Contact.last_name.ilike(search_pattern),
                Contact.email.ilike(search_pattern)
            )
        )
    stmt = stmt.order_by(Contact.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contact_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    contact_id: uuid.UUID
) -> Contact:
    """Fetches a contact by ID within tenant scope (raises 404 if missing or cross-tenant)."""
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.organization_id == organization_id
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundException("Contact requested was not found")
    return contact


async def update_contact(
    db: AsyncSession,
    organization_id: uuid.UUID,
    contact_id: uuid.UUID,
    payload: ContactUpdate
) -> Contact:
    """Updates a contact record within the tenant scope."""
    contact = await get_contact_by_id(db, organization_id, contact_id)
    update_data = payload.model_dump(exclude_unset=True)

    # If customer_id is being changed, verify the NEW customer belongs to tenant
    if "customer_id" in update_data and update_data["customer_id"] is not None:
        await verify_customer_in_tenant(db, organization_id, update_data["customer_id"])

    for field, value in update_data.items():
        setattr(contact, field, value)
    await db.flush()
    return contact


async def delete_contact(
    db: AsyncSession,
    organization_id: uuid.UUID,
    contact_id: uuid.UUID
) -> None:
    """Deletes a contact record within the tenant scope."""
    contact = await get_contact_by_id(db, organization_id, contact_id)
    await db.delete(contact)
    await db.flush()
