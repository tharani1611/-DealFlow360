import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.core.exceptions import NotFoundException

logger = logging.getLogger("dealflow360.customers_service")


async def create_customer(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: CustomerCreate
) -> Customer:
    """Creates a new Customer record tied exclusively to the user's organization."""
    customer = Customer(
        organization_id=organization_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        postal_code=payload.postal_code,
        is_active=payload.is_active
    )
    db.add(customer)
    await db.flush()
    return customer


async def list_customers(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[Customer]:
    """Retrieves customers scoped strictly to the specified organization."""
    stmt = select(Customer).where(Customer.organization_id == organization_id)
    if is_active is not None:
        stmt = stmt.where(Customer.is_active == is_active)
    if search:
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.where(Customer.name.ilike(search_pattern))
    stmt = stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_customer_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID
) -> Customer:
    """Fetches a specific customer by ID within the tenant scope (raises 404 if missing or cross-tenant)."""
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer requested was not found")
    return customer


async def update_customer(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    payload: CustomerUpdate
) -> Customer:
    """Updates a customer record within the tenant scope."""
    customer = await get_customer_by_id(db, organization_id, customer_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    await db.flush()
    return customer


async def delete_customer(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID
) -> None:
    """Deletes a customer record within the tenant scope."""
    customer = await get_customer_by_id(db, organization_id, customer_id)
    await db.delete(customer)
    await db.flush()
