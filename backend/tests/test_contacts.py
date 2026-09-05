import pytest
import uuid
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact


@pytest.mark.asyncio
async def test_create_contact_success(async_client: AsyncClient):
    """Verify creating contact linked to customer in same organization."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Contact Create Org",
        "organization_slug": f"cnt-create-{uuid.uuid4().hex[:8]}",
        "email": "admin@cntcreate.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Customer first
    cust_resp = await async_client.post("/api/v1/customers", json={"name": "Acme Partner"}, headers=headers)
    cust_id = cust_resp.json()["id"]

    # Create Contact
    contact_payload = {
        "customer_id": cust_id,
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@acmepartner.com",
        "phone": "+1-555-0188",
        "job_title": "VP Procurement",
        "is_primary": True
    }
    resp = await async_client.post("/api/v1/contacts", json=contact_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["customer_id"] == cust_id
    assert data["organization_id"] == org_id
    assert data["is_primary"] is True


@pytest.mark.asyncio
async def test_create_contact_blank_first_name_rejected(async_client: AsyncClient):
    """Verify empty/whitespace first name is rejected with 422."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Blank Contact Org",
        "organization_slug": f"blank-cnt-{uuid.uuid4().hex[:8]}",
        "email": "admin@blankcnt.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_resp = await async_client.post("/api/v1/customers", json={"name": "Customer X"}, headers=headers)
    cust_id = cust_resp.json()["id"]

    payload = {
        "customer_id": cust_id,
        "first_name": "   ",
        "email": "test@test.com"
    }
    resp = await async_client.post("/api/v1/contacts", json=payload, headers=headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_and_filter_contacts(async_client: AsyncClient):
    """Verify listing contacts with customer_id and search filters."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "List Contact Org",
        "organization_slug": f"list-cnt-{uuid.uuid4().hex[:8]}",
        "email": "admin@listcnt.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c1 = (await async_client.post("/api/v1/customers", json={"name": "Cust 1"}, headers=headers)).json()["id"]
    c2 = (await async_client.post("/api/v1/customers", json={"name": "Cust 2"}, headers=headers)).json()["id"]

    await async_client.post("/api/v1/contacts", json={"customer_id": c1, "first_name": "Bob", "last_name": "Marley"}, headers=headers)
    await async_client.post("/api/v1/contacts", json={"customer_id": c2, "first_name": "Charlie", "last_name": "Brown"}, headers=headers)

    # Filter by customer_id
    res_c1 = await async_client.get(f"/api/v1/contacts?customer_id={c1}", headers=headers)
    assert res_c1.status_code == 200
    assert len(res_c1.json()) == 1
    assert res_c1.json()[0]["first_name"] == "Bob"

    # Search filter
    res_search = await async_client.get("/api/v1/contacts?search=brown", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["first_name"] == "Charlie"


@pytest.mark.asyncio
async def test_get_and_update_contact(async_client: AsyncClient):
    """Verify GET and PUT contact within tenant scope."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Update Contact Org",
        "organization_slug": f"upd-cnt-{uuid.uuid4().hex[:8]}",
        "email": "admin@updcnt.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_id = (await async_client.post("/api/v1/customers", json={"name": "Cust"}, headers=headers)).json()["id"]
    cnt_id = (await async_client.post("/api/v1/contacts", json={"customer_id": c_id, "first_name": "David"}, headers=headers)).json()["id"]

    # GET
    get_res = await async_client.get(f"/api/v1/contacts/{cnt_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["first_name"] == "David"

    # PUT
    put_res = await async_client.put(f"/api/v1/contacts/{cnt_id}", json={"first_name": "David", "last_name": "Beckham", "job_title": "Director"}, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["last_name"] == "Beckham"
    assert put_res.json()["job_title"] == "Director"


@pytest.mark.asyncio
async def test_delete_contact_authorization(async_client: AsyncClient):
    """Verify DELETE contact succeeds for Admin (204) and is forbidden for regular user (403)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Del Contact Org",
        "organization_slug": f"del-cnt-{uuid.uuid4().hex[:8]}",
        "email": "admin@delcnt.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular user
    async with AsyncSessionLocal() as session:
        reg_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@delcnt.com",
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

    c_id = (await async_client.post("/api/v1/customers", json={"name": "Cust"}, headers=headers_norm)).json()["id"]
    cnt_id = (await async_client.post("/api/v1/contacts", json={"customer_id": c_id, "first_name": "Eve"}, headers=headers_norm)).json()["id"]

    # Regular user DELETE -> 403
    del_norm = await async_client.delete(f"/api/v1/contacts/{cnt_id}", headers=headers_norm)
    assert del_norm.status_code == 403

    # Admin DELETE -> 204
    del_admin = await async_client.delete(f"/api/v1/contacts/{cnt_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_admin.status_code == 204


@pytest.mark.asyncio
async def test_cross_tenant_contact_attack_prevention(async_client: AsyncClient):
    """
    CRITICAL TENANT ISOLATION TEST FOR CONTACTS:
    1. User A cannot GET, PUT, or DELETE Contact B (Org B).
    2. User A cannot create a contact linked to Customer B (Org B).
    3. User A cannot update Contact A to reassign customer_id to Customer B (Org B).
    Returns 404 Not Found.
    """
    slug_a = f"cnt-tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"cnt-tenant-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Contact Tenant A",
        "organization_slug": slug_a,
        "email": "userA@cnttenanta.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Contact Tenant B",
        "organization_slug": slug_b,
        "email": "userB@cnttenantb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Setup Tenant A Customer & Contact
    cust_a_id = (await async_client.post("/api/v1/customers", json={"name": "Customer A"}, headers=headers_a)).json()["id"]
    cnt_a_id = (await async_client.post("/api/v1/contacts", json={"customer_id": cust_a_id, "first_name": "Contact A"}, headers=headers_a)).json()["id"]

    # Setup Tenant B Customer & Contact
    cust_b_id = (await async_client.post("/api/v1/customers", json={"name": "Customer B"}, headers=headers_b)).json()["id"]
    cnt_b_id = (await async_client.post("/api/v1/contacts", json={"customer_id": cust_b_id, "first_name": "Contact B"}, headers=headers_b)).json()["id"]

    # Attack 1: User A GET Contact B -> 404
    get_cross = await async_client.get(f"/api/v1/contacts/{cnt_b_id}", headers=headers_a)
    assert get_cross.status_code == 404

    # Attack 2: User A PUT Contact B -> 404
    put_cross = await async_client.put(f"/api/v1/contacts/{cnt_b_id}", json={"first_name": "Hacked Contact"}, headers=headers_a)
    assert put_cross.status_code == 404

    # Attack 3: User A DELETE Contact B -> 404
    del_cross = await async_client.delete(f"/api/v1/contacts/{cnt_b_id}", headers=headers_a)
    assert del_cross.status_code == 404

    # Attack 4: User A creates contact linked to Customer B (Org B) -> 404
    create_cross = await async_client.post("/api/v1/contacts", json={"customer_id": cust_b_id, "first_name": "Spy Contact"}, headers=headers_a)
    assert create_cross.status_code == 404

    # Attack 5: User A updates Contact A to switch customer_id to Customer B (Org B) -> 404
    reassign_cross = await async_client.put(f"/api/v1/contacts/{cnt_a_id}", json={"customer_id": cust_b_id}, headers=headers_a)
    assert reassign_cross.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_contact_endpoints_rejected(async_client: AsyncClient):
    """Verify anonymous access to contact endpoints returns 401 Unauthorized."""
    fake_id = str(uuid.uuid4())
    assert (await async_client.get("/api/v1/contacts")).status_code == 401
    assert (await async_client.post("/api/v1/contacts", json={"customer_id": fake_id, "first_name": "Test"})).status_code == 401
    assert (await async_client.get(f"/api/v1/contacts/{fake_id}")).status_code == 401
    assert (await async_client.put(f"/api/v1/contacts/{fake_id}", json={"first_name": "Test"})).status_code == 401
    assert (await async_client.delete(f"/api/v1/contacts/{fake_id}")).status_code == 401
