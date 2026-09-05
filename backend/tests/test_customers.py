import pytest
import uuid
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.customer import Customer


@pytest.mark.asyncio
async def test_create_customer_success(async_client: AsyncClient):
    """Verify authenticated user can create a customer successfully."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Cust Create Org",
        "organization_slug": f"cust-create-{uuid.uuid4().hex[:8]}",
        "email": "admin@custcreate.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Global Logistics Inc",
        "email": "info@globallogistics.com",
        "phone": "+1-555-0199",
        "address": "100 Fleet Street",
        "city": "Metropolis",
        "state": "NY",
        "country": "USA",
        "postal_code": "10001",
        "is_active": True
    }

    resp = await async_client.post("/api/v1/customers", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["name"] == "Global Logistics Inc"
    assert data["email"] == "info@globallogistics.com"
    assert data["organization_id"] == org_id
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_customer_blank_name_rejected(async_client: AsyncClient):
    """Verify empty/whitespace customer name is rejected with 422 Unprocessable Entity."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Blank Cust Org",
        "organization_slug": f"blank-cust-{uuid.uuid4().hex[:8]}",
        "email": "admin@blankcust.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": "   ", "email": "info@test.com"}
    resp = await async_client.post("/api/v1/customers", json=payload, headers=headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_and_search_customers(async_client: AsyncClient):
    """Verify listing and searching customers scoped strictly to the current organization."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "List Cust Org",
        "organization_slug": f"list-cust-{uuid.uuid4().hex[:8]}",
        "email": "admin@listcust.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create 2 customers
    await async_client.post("/api/v1/customers", json={"name": "Alpha Corp"}, headers=headers)
    await async_client.post("/api/v1/customers", json={"name": "Beta Services"}, headers=headers)

    # List all
    resp = await async_client.get("/api/v1/customers", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2

    # Search filter
    search_resp = await async_client.get("/api/v1/customers?search=alpha", headers=headers)
    assert search_resp.status_code == 200
    search_items = search_resp.json()
    assert len(search_items) == 1
    assert search_items[0]["name"] == "Alpha Corp"


@pytest.mark.asyncio
async def test_get_and_update_customer(async_client: AsyncClient):
    """Verify fetching and updating customer details within tenant."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Update Cust Org",
        "organization_slug": f"upd-cust-{uuid.uuid4().hex[:8]}",
        "email": "admin@updcust.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post("/api/v1/customers", json={"name": "Original Name"}, headers=headers)
    cust_id = create_resp.json()["id"]

    # GET details
    get_resp = await async_client.get(f"/api/v1/customers/{cust_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Original Name"

    # PUT update
    put_resp = await async_client.put(f"/api/v1/customers/{cust_id}", json={"name": "Updated Name", "city": "Boston"}, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Updated Name"
    assert put_resp.json()["city"] == "Boston"


@pytest.mark.asyncio
async def test_delete_customer_authorization(async_client: AsyncClient):
    """Verify DELETE customer succeeds for Admin (204) and is forbidden for non-admin (403)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Del Cust Org",
        "organization_slug": f"del-cust-{uuid.uuid4().hex[:8]}",
        "email": "admin@delcust.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular non-admin user
    async with AsyncSessionLocal() as session:
        reg_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@delcust.com",
            password_hash=hash_password("Password123!"),
            is_admin=False,
            is_active=True
        )
        session.add(reg_user)
        await session.commit()
        await session.refresh(reg_user)
        reg_user_id = str(reg_user.id)

    normal_token = create_access_token(subject=reg_user_id)

    # Create customer as normal user
    create_resp = await async_client.post("/api/v1/customers", json={"name": "To Delete Inc"}, headers={"Authorization": f"Bearer {normal_token}"})
    cust_id = create_resp.json()["id"]

    # Normal user attempts DELETE -> 403 Forbidden
    del_norm = await async_client.delete(f"/api/v1/customers/{cust_id}", headers={"Authorization": f"Bearer {normal_token}"})
    assert del_norm.status_code == 403

    # Admin attempts DELETE -> 204 No Content
    del_admin = await async_client.delete(f"/api/v1/customers/{cust_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_admin.status_code == 204


@pytest.mark.asyncio
async def test_cross_tenant_customer_attack_prevention(async_client: AsyncClient):
    """
    CRITICAL TENANT ISOLATION TEST:
    Verify User A (Org A) cannot GET, PUT, or DELETE Customer B (Org B). Returns 404 Not Found.
    """
    slug_a = f"tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"tenant-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant A",
        "organization_slug": slug_a,
        "email": "userA@tenanta.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant B",
        "organization_slug": slug_b,
        "email": "userB@tenantb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]

    # Create Customer B in Tenant B
    create_b = await async_client.post("/api/v1/customers", json={"name": "Secret Customer B"}, headers={"Authorization": f"Bearer {token_b}"})
    cust_b_id = create_b.json()["id"]

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A tries GET Customer B -> 404
    get_cross = await async_client.get(f"/api/v1/customers/{cust_b_id}", headers=headers_a)
    assert get_cross.status_code == 404

    # User A tries PUT Customer B -> 404
    put_cross = await async_client.put(f"/api/v1/customers/{cust_b_id}", json={"name": "Hacked Name"}, headers=headers_a)
    assert put_cross.status_code == 404

    # User A tries DELETE Customer B -> 404
    del_cross = await async_client.delete(f"/api/v1/customers/{cust_b_id}", headers=headers_a)
    assert del_cross.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_customer_endpoints_rejected(async_client: AsyncClient):
    """Verify anonymous access to customer endpoints returns 401 Unauthorized."""
    fake_id = str(uuid.uuid4())
    assert (await async_client.get("/api/v1/customers")).status_code == 401
    assert (await async_client.post("/api/v1/customers", json={"name": "Test"})).status_code == 401
    assert (await async_client.get(f"/api/v1/customers/{fake_id}")).status_code == 401
    assert (await async_client.put(f"/api/v1/customers/{fake_id}", json={"name": "Test"})).status_code == 401
    assert (await async_client.delete(f"/api/v1/customers/{fake_id}")).status_code == 401
