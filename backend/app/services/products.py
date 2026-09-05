import uuid
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.exceptions import NotFoundException, ConflictException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.products_service")


async def create_product(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: ProductCreate
) -> Product:
    """Creates a new Product record scoped strictly to the specified organization."""
    sku = payload.sku.strip().upper()

    # Pre-check for SKU uniqueness within the organization
    existing_stmt = select(Product).where(
        Product.organization_id == organization_id,
        Product.sku == sku
    )
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise ConflictException(f"Product SKU '{sku}' already exists in this organization.")

    product = Product(
        organization_id=organization_id,
        name=payload.name.strip(),
        sku=sku,
        description=payload.description.strip() if payload.description else None,
        unit_price=payload.unit_price,
        unit_cost=payload.unit_cost,
        currency=payload.currency.strip().upper(),
        is_active=payload.is_active
    )

    try:
        db.add(product)
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        error_msg = str(exc)
        logger.warning(f"Product creation failed for SKU '{sku}': {error_msg}")
        if "uq_products_organization_id_sku" in error_msg or "sku" in error_msg:
            raise ConflictException(f"Product SKU '{sku}' already exists in this organization.")
        if "unit_price_non_negative" in error_msg or "unit_price" in error_msg:
            raise BusinessRuleViolationException("Product unit price must be non-negative.")
        raise BusinessRuleViolationException("Product creation failed due to a database constraint violation.")

    return product


async def list_products(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sku: Optional[str] = None,
    currency: Optional[str] = None
) -> List[Product]:
    """Retrieves products scoped strictly to the specified organization."""
    stmt = select(Product).where(Product.organization_id == organization_id)

    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
    if sku:
        stmt = stmt.where(Product.sku == sku.strip().upper())
    if currency:
        stmt = stmt.where(Product.currency == currency.strip().upper())
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern)
            )
        )

    stmt = stmt.order_by(Product.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    product_id: uuid.UUID
) -> Product:
    """Fetches a product by ID within tenant scope (raises 404 if missing or cross-tenant)."""
    stmt = select(Product).where(
        Product.id == product_id,
        Product.organization_id == organization_id
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product requested was not found")
    return product


async def update_product(
    db: AsyncSession,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductUpdate
) -> Product:
    """Updates a product record within the tenant scope."""
    product = await get_product_by_id(db, organization_id, product_id)
    update_data = payload.model_dump(exclude_unset=True)

    # If SKU is being updated to a different value, check for duplicate within the tenant
    if "sku" in update_data and update_data["sku"] is not None:
        new_sku = update_data["sku"].strip().upper()
        if new_sku != product.sku:
            existing_stmt = select(Product).where(
                Product.organization_id == organization_id,
                Product.sku == new_sku,
                Product.id != product_id
            )
            existing_res = await db.execute(existing_stmt)
            if existing_res.scalar_one_or_none():
                raise ConflictException(f"Product SKU '{new_sku}' already exists in this organization.")
            update_data["sku"] = new_sku

    if "name" in update_data and update_data["name"]:
        update_data["name"] = update_data["name"].strip()
    if "currency" in update_data and update_data["currency"]:
        update_data["currency"] = update_data["currency"].strip().upper()

    try:
        for field, value in update_data.items():
            setattr(product, field, value)
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        error_msg = str(exc)
        if "uq_products_organization_id_sku" in error_msg or "sku" in error_msg:
            raise ConflictException(f"Product SKU '{update_data.get('sku')}' already exists in this organization.")
        if "unit_price_non_negative" in error_msg:
            raise BusinessRuleViolationException("Product unit price must be non-negative.")
        raise BusinessRuleViolationException("Product update failed due to a database constraint violation.")

    return product


async def delete_product(
    db: AsyncSession,
    organization_id: uuid.UUID,
    product_id: uuid.UUID
) -> None:
    """Deletes a product record within the tenant scope."""
    product = await get_product_by_id(db, organization_id, product_id)
    await db.delete(product)
    await db.flush()
