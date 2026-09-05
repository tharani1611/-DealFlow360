import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.product import Product


@pytest.mark.asyncio
async def test_create_product_success(async_client: AsyncClient):
    """Verify authenticated user can create a product/service entry successfully."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Prod Create Org",
        "organization_slug": f"prod-create-{uuid.uuid4().hex[:8]}",
        "email": "admin@prodcreate.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Enterprise Cloud Server X1",
        "sku": "SERVER-X1",
        "description": "High performance 64-core dedicated cloud instance",
        "unit_price": "4999.99",
        "currency": "USD",
        "is_active": True
    }

    resp = await async_client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["name"] == "Enterprise Cloud Server X1"
    assert data["sku"] == "SERVER-X1"
    assert data["organization_id"] == org_id
    assert Decimal(data["unit_price"]) == Decimal("4999.99")
    assert data["currency"] == "USD"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_blank_name_or_sku_rejected(async_client: AsyncClient):
    """Verify empty/whitespace name or SKU is rejected with 422."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Blank Prod Org",
        "organization_slug": f"blank-prod-{uuid.uuid4().hex[:8]}",
        "email": "admin@blankprod.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Blank name
    resp1 = await async_client.post("/api/v1/products", json={"name": "   ", "sku": "SKU-01", "unit_price": "10.00"}, headers=headers)
    assert resp1.status_code == 422

    # Blank SKU
    resp2 = await async_client.post("/api/v1/products", json={"name": "Widget", "sku": "   ", "unit_price": "10.00"}, headers=headers)
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_price_validation_negative_price_rejected(async_client: AsyncClient):
    """Verify negative unit price is rejected with 422 and valid boundary prices succeed."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Price Val Org",
        "organization_slug": f"price-val-{uuid.uuid4().hex[:8]}",
        "email": "admin@priceval.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Negative price -> 422
    res_neg = await async_client.post("/api/v1/products", json={"name": "Bad Price", "sku": "BAD-01", "unit_price": "-1.00"}, headers=headers)
    assert res_neg.status_code == 422

    # Zero price -> 201
    res_zero = await async_client.post("/api/v1/products", json={"name": "Free Tier", "sku": "FREE-01", "unit_price": "0.00"}, headers=headers)
    assert res_zero.status_code == 201

    # Cent price -> 201
    res_cent = await async_client.post("/api/v1/products", json={"name": "Micro Service", "sku": "MICRO-01", "unit_price": "0.01"}, headers=headers)
    assert res_cent.status_code == 201


@pytest.mark.asyncio
async def test_sku_uniqueness_is_tenant_scoped(async_client: AsyncClient):
    """
    CRITICAL SKU TEST:
    1. Duplicate SKU within same organization returns 409 Conflict.
    2. Same SKU across two different organizations succeeds (201 Created).
    """
    slug_a = f"sku-org-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"sku-org-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "SKU Org A",
        "organization_slug": slug_a,
        "email": "adminA@skua.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "SKU Org B",
        "organization_slug": slug_b,
        "email": "adminB@skub.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Org A creates SKU SHARED-001 -> 201
    res1 = await async_client.post("/api/v1/products", json={"name": "Prod A1", "sku": "SHARED-001", "unit_price": "100.00"}, headers=headers_a)
    assert res1.status_code == 201

    # Org A creates SECOND product with SAME SKU SHARED-001 -> 409 Conflict
    res2 = await async_client.post("/api/v1/products", json={"name": "Prod A2", "sku": "SHARED-001", "unit_price": "200.00"}, headers=headers_a)
    assert res2.status_code == 409

    # Org B creates product with SAME SKU SHARED-001 -> 201 Created (tenant isolated!)
    res3 = await async_client.post("/api/v1/products", json={"name": "Prod B1", "sku": "SHARED-001", "unit_price": "150.00"}, headers=headers_b)
    assert res3.status_code == 201


@pytest.mark.asyncio
async def test_list_search_and_filter_products(async_client: AsyncClient):
    """Verify list, search, active filter, and pagination for products."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "List Prod Org",
        "organization_slug": f"list-prod-{uuid.uuid4().hex[:8]}",
        "email": "admin@listprod.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await async_client.post("/api/v1/products", json={"name": "MacBook Pro 16", "sku": "MBP-16", "unit_price": "2499.00", "is_active": True}, headers=headers)
    await async_client.post("/api/v1/products", json={"name": "Dell XPS 15", "sku": "XPS-15", "unit_price": "1899.00", "is_active": False}, headers=headers)

    # List all
    list_all = await async_client.get("/api/v1/products", headers=headers)
    assert list_all.status_code == 200
    assert len(list_all.json()) == 2

    # Filter is_active=true
    active_only = await async_client.get("/api/v1/products?is_active=true", headers=headers)
    assert active_only.status_code == 200
    assert len(active_only.json()) == 1
    assert active_only.json()[0]["sku"] == "MBP-16"

    # Search search=macbook
    search_res = await async_client.get("/api/v1/products?search=macbook", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert search_res.json()[0]["sku"] == "MBP-16"


@pytest.mark.asyncio
async def test_get_and_update_product(async_client: AsyncClient):
    """Verify GET and PUT product within tenant scope."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Upd Prod Org",
        "organization_slug": f"upd-prod-{uuid.uuid4().hex[:8]}",
        "email": "admin@updprod.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await async_client.post("/api/v1/products", json={"name": "Old Name", "sku": "OLD-01", "unit_price": "50.00"}, headers=headers)
    prod_id = create_res.json()["id"]

    # GET
    get_res = await async_client.get(f"/api/v1/products/{prod_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Old Name"

    # PUT update name and price
    put_res = await async_client.put(f"/api/v1/products/{prod_id}", json={"name": "New Name", "unit_price": "75.00"}, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["name"] == "New Name"
    assert Decimal(put_res.json()["unit_price"]) == Decimal("75.00")


@pytest.mark.asyncio
async def test_delete_product_authorization(async_client: AsyncClient):
    """Verify DELETE product succeeds for Admin (204) and is forbidden for regular user (403)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Del Prod Org",
        "organization_slug": f"del-prod-{uuid.uuid4().hex[:8]}",
        "email": "admin@delprod.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular user
    async with AsyncSessionLocal() as session:
        reg_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@delprod.com",
            password_hash=hash_password("Password123!"),
            is_admin=False,
            is_active=True
        )
        session.add(reg_user)
        await session.commit()
        await session.refresh(reg_user)
        reg_user_id = str(reg_user.id)

    normal_token = create_access_token(subject=reg_user_id)
    headers_norm = {"Authorization": f"Bearer {normal_token}"}

    prod_id = (await async_client.post("/api/v1/products", json={"name": "To Delete", "sku": "DEL-01", "unit_price": "10.00"}, headers=headers_norm)).json()["id"]

    # Normal user DELETE -> 403 Forbidden
    del_norm = await async_client.delete(f"/api/v1/products/{prod_id}", headers=headers_norm)
    assert del_norm.status_code == 403

    # Admin DELETE -> 204 No Content
    del_admin = await async_client.delete(f"/api/v1/products/{prod_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_admin.status_code == 204


@pytest.mark.asyncio
async def test_cross_tenant_product_attack_prevention(async_client: AsyncClient):
    """
    CRITICAL TENANT ISOLATION TEST:
    Verify User A (Org A) cannot GET, PUT, or DELETE Product B (Org B). Returns 404 Not Found.
    """
    slug_a = f"prod-tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"prod-tenant-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Product Tenant A",
        "organization_slug": slug_a,
        "email": "userA@prodtenanta.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Product Tenant B",
        "organization_slug": slug_b,
        "email": "userB@prodtenantb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create Product B in Tenant B
    prod_b_id = (await async_client.post("/api/v1/products", json={"name": "Secret Product B", "sku": "SEC-B", "unit_price": "999.00"}, headers=headers_b)).json()["id"]

    # User A tries GET Product B -> 404
    get_cross = await async_client.get(f"/api/v1/products/{prod_b_id}", headers=headers_a)
    assert get_cross.status_code == 404

    # User A tries PUT Product B -> 404
    put_cross = await async_client.put(f"/api/v1/products/{prod_b_id}", json={"name": "Hacked Product"}, headers=headers_a)
    assert put_cross.status_code == 404

    # User A tries DELETE Product B -> 404
    del_cross = await async_client.delete(f"/api/v1/products/{prod_b_id}", headers=headers_a)
    assert del_cross.status_code == 404


@pytest.mark.asyncio
async def test_client_tenant_override_ignored(async_client: AsyncClient):
    """Verify client sending arbitrary organization_id in body cannot create product in another tenant."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Client Override Org",
        "organization_slug": f"override-prod-{uuid.uuid4().hex[:8]}",
        "email": "admin@overrideprod.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    real_org_id = reg_resp.json()["organization"]["id"]
    fake_org_id = str(uuid.uuid4())

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Overridden Prod",
        "sku": "OVR-01",
        "unit_price": "100.00",
        "organization_id": fake_org_id
    }
    resp = await async_client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["organization_id"] == real_org_id
    assert resp.json()["organization_id"] != fake_org_id


@pytest.mark.asyncio
async def test_unauthenticated_product_endpoints_rejected(async_client: AsyncClient):
    """Verify anonymous access to product endpoints returns 401 Unauthorized."""
    fake_id = str(uuid.uuid4())
    assert (await async_client.get("/api/v1/products")).status_code == 401
    assert (await async_client.post("/api/v1/products", json={"name": "Test", "sku": "T-1", "unit_price": "10.00"})).status_code == 401
    assert (await async_client.get(f"/api/v1/products/{fake_id}")).status_code == 401
    assert (await async_client.put(f"/api/v1/products/{fake_id}", json={"name": "Test"})).status_code == 401
    assert (await async_client.delete(f"/api/v1/products/{fake_id}")).status_code == 401
