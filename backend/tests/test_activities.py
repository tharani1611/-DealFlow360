import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_unauthenticated_activity_endpoints_rejected(async_client: AsyncClient):
    """Verify anonymous access to activity endpoints returns 401 Unauthorized."""
    fake_id = str(uuid.uuid4())
    assert (await async_client.get("/api/v1/activities")).status_code == 401
    assert (await async_client.post("/api/v1/activities", json={"activity_type": "task", "title": "Test"})).status_code == 401
    assert (await async_client.get(f"/api/v1/activities/{fake_id}")).status_code == 401
    assert (await async_client.put(f"/api/v1/activities/{fake_id}", json={"title": "Test"})).status_code == 401
    assert (await async_client.post(f"/api/v1/activities/{fake_id}/complete")).status_code == 401
    assert (await async_client.post(f"/api/v1/activities/{fake_id}/cancel")).status_code == 401
    assert (await async_client.delete(f"/api/v1/activities/{fake_id}")).status_code == 401


@pytest.mark.asyncio
async def test_create_activity_types_and_defaults(async_client: AsyncClient):
    """Verify creating activities with valid types, priorities, and default pending status."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Act Create Org",
        "organization_slug": f"act-create-{uuid.uuid4().hex[:8]}",
        "email": "admin@actcreate.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    types = ["task", "call", "meeting", "note", "follow_up"]
    for atype in types:
        payload = {
            "activity_type": atype,
            "title": f"Sample {atype} title",
            "description": f"Details for {atype}",
            "priority": "high"
        }
        resp = await async_client.post("/api/v1/activities", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()

        assert data["activity_type"] == atype
        assert data["title"] == f"Sample {atype} title"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert data["created_by_user_id"] == user_id
        assert data["organization_id"] == org_id
        assert data["completed_at"] is None


@pytest.mark.asyncio
async def test_invalid_activity_type_and_priority_rejected(async_client: AsyncClient):
    """Verify invalid activity_type or priority returns 422 Unprocessable Entity."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Act Val Org",
        "organization_slug": f"act-val-{uuid.uuid4().hex[:8]}",
        "email": "admin@actval.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Bad activity type
    r1 = await async_client.post("/api/v1/activities", json={"activity_type": "invalid_type", "title": "Test"}, headers=headers)
    assert r1.status_code == 422

    # Bad priority
    r2 = await async_client.post("/api/v1/activities", json={"activity_type": "task", "title": "Test", "priority": "invalid_priority"}, headers=headers)
    assert r2.status_code == 422


@pytest.mark.asyncio
async def test_relationship_validations_and_mismatches(async_client: AsyncClient):
    """Verify relationships with customer, contact, deal, quotation, and assigned user."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Act Rel Org",
        "organization_slug": f"act-rel-{uuid.uuid4().hex[:8]}",
        "email": "admin@actrel.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    cust1_id = (await async_client.post("/api/v1/customers", json={"name": "Customer 1"}, headers=headers)).json()["id"]
    cust2_id = (await async_client.post("/api/v1/customers", json={"name": "Customer 2"}, headers=headers)).json()["id"]

    contact2_id = (await async_client.post("/api/v1/contacts", json={"customer_id": cust2_id, "first_name": "Jane"}, headers=headers)).json()["id"]
    deal2_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust2_id, "title": "Deal 2"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "P1", "unit_price": "100.00"}, headers=headers)).json()["id"]
    quot2_id = (await async_client.post("/api/v1/quotations", json={"customer_id": cust2_id, "items": [{"product_id": prod_id, "quantity": "1"}]}, headers=headers)).json()["id"]

    # Valid association with Customer 1
    ok_resp = await async_client.post("/api/v1/activities", json={
        "activity_type": "task",
        "title": "Cust 1 Task",
        "customer_id": cust1_id,
        "assigned_to_user_id": user_id
    }, headers=headers)
    assert ok_resp.status_code == 201

    # Contact mismatch (Cust 1 activity + Cust 2 contact) -> 404
    r_ct = await async_client.post("/api/v1/activities", json={"activity_type": "call", "title": "Mismatch", "customer_id": cust1_id, "contact_id": contact2_id}, headers=headers)
    assert r_ct.status_code == 404

    # Deal mismatch (Cust 1 activity + Cust 2 deal) -> 404
    r_d = await async_client.post("/api/v1/activities", json={"activity_type": "call", "title": "Mismatch", "customer_id": cust1_id, "deal_id": deal2_id}, headers=headers)
    assert r_d.status_code == 404

    # Quotation mismatch (Cust 1 activity + Cust 2 quotation) -> 404
    r_q = await async_client.post("/api/v1/activities", json={"activity_type": "call", "title": "Mismatch", "customer_id": cust1_id, "quotation_id": quot2_id}, headers=headers)
    assert r_q.status_code == 404


@pytest.mark.asyncio
async def test_inactive_user_assignment_rejected(async_client: AsyncClient):
    """Verify assigning activity to an inactive user returns 404 Not Found."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Inact Assign Org",
        "organization_slug": f"inact-assign-{uuid.uuid4().hex[:8]}",
        "email": "admin@inactassign.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create inactive user
    async with AsyncSessionLocal() as session:
        inact_user = User(
            organization_id=uuid.UUID(org_id),
            email="inactive@inactassign.com",
            password_hash=hash_password("Password123!"),
            is_active=False
        )
        session.add(inact_user)
        await session.commit()
        await session.refresh(inact_user)
        inact_user_id = str(inact_user.id)

    res = await async_client.post("/api/v1/activities", json={
        "activity_type": "task",
        "title": "Task for Inactive",
        "assigned_to_user_id": inact_user_id
    }, headers=headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_completion_and_cancellation_state_machine(async_client: AsyncClient):
    """Verify completing activity sets completed_at server-side and blocks further modifications."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "State Org",
        "organization_slug": f"state-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@stateorg.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Complete workflow
    act1 = (await async_client.post("/api/v1/activities", json={"activity_type": "task", "title": "Task 1"}, headers=headers)).json()["id"]
    comp_res = await async_client.post(f"/api/v1/activities/{act1}/complete", headers=headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"
    assert comp_res.json()["completed_at"] is not None

    # Re-completing completed activity -> 422 BusinessRuleViolation
    re_comp = await async_client.post(f"/api/v1/activities/{act1}/complete", headers=headers)
    assert re_comp.status_code == 422

    # Updating completed activity -> 422 BusinessRuleViolation
    mod_comp = await async_client.put(f"/api/v1/activities/{act1}", json={"title": "Hacked Title"}, headers=headers)
    assert mod_comp.status_code == 422

    # 2. Cancel workflow
    act2 = (await async_client.post("/api/v1/activities", json={"activity_type": "call", "title": "Task 2"}, headers=headers)).json()["id"]
    can_res = await async_client.post(f"/api/v1/activities/{act2}/cancel", headers=headers)
    assert can_res.status_code == 200
    assert can_res.json()["status"] == "cancelled"

    # Re-cancelling cancelled activity -> 422 BusinessRuleViolation
    re_can = await async_client.post(f"/api/v1/activities/{act2}/cancel", headers=headers)
    assert re_can.status_code == 422


@pytest.mark.asyncio
async def test_overdue_and_upcoming_filters(async_client: AsyncClient):
    """Verify overdue=true and upcoming=true query filters."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Date Filter Org",
        "organization_slug": f"date-filter-{uuid.uuid4().hex[:8]}",
        "email": "admin@datefilter.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    future_due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    overdue_act_id = (await async_client.post("/api/v1/activities", json={
        "activity_type": "task",
        "title": "Overdue Task",
        "due_at": past_due
    }, headers=headers)).json()["id"]

    upcoming_act_id = (await async_client.post("/api/v1/activities", json={
        "activity_type": "meeting",
        "title": "Upcoming Meeting",
        "due_at": future_due
    }, headers=headers)).json()["id"]

    # Query overdue=true
    overdue_res = await async_client.get("/api/v1/activities?overdue=true", headers=headers)
    assert overdue_res.status_code == 200
    assert len(overdue_res.json()) == 1
    assert overdue_res.json()[0]["id"] == overdue_act_id

    # Query upcoming=true
    upcoming_res = await async_client.get("/api/v1/activities?upcoming=true", headers=headers)
    assert upcoming_res.status_code == 200
    assert len(upcoming_res.json()) == 1
    assert upcoming_res.json()[0]["id"] == upcoming_act_id


@pytest.mark.asyncio
async def test_customer_and_deal_timeline_endpoints(async_client: AsyncClient):
    """Verify GET /api/v1/customers/{id}/activities and GET /api/v1/deals/{id}/activities timelines."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Timeline Org",
        "organization_slug": f"timeline-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@timelineorg.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Timeline Cust"}, headers=headers)).json()["id"]
    deal_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Timeline Deal"}, headers=headers)).json()["id"]

    a1 = (await async_client.post("/api/v1/activities", json={"activity_type": "note", "title": "Note 1", "customer_id": cust_id, "deal_id": deal_id}, headers=headers)).json()["id"]
    a2 = (await async_client.post("/api/v1/activities", json={"activity_type": "call", "title": "Call 1", "customer_id": cust_id, "deal_id": deal_id}, headers=headers)).json()["id"]

    # Customer timeline
    cust_t = await async_client.get(f"/api/v1/customers/{cust_id}/activities", headers=headers)
    assert cust_t.status_code == 200
    assert len(cust_t.json()) == 2
    # Newest first
    assert cust_t.json()[0]["id"] == a2
    assert cust_t.json()[1]["id"] == a1

    # Deal timeline
    deal_t = await async_client.get(f"/api/v1/deals/{deal_id}/activities", headers=headers)
    assert deal_t.status_code == 200
    assert len(deal_t.json()) == 2
    assert deal_t.json()[0]["id"] == a2


@pytest.mark.asyncio
async def test_delete_activity_admin_authorization(async_client: AsyncClient):
    """Verify DELETE activity succeeds for Admin (204) and is forbidden for regular user (403)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Del Act Org",
        "organization_slug": f"del-act-{uuid.uuid4().hex[:8]}",
        "email": "admin@delact.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular user
    async with AsyncSessionLocal() as session:
        reg_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@delact.com",
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
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    act_id = (await async_client.post("/api/v1/activities", json={"activity_type": "task", "title": "To Delete"}, headers=headers_admin)).json()["id"]

    # Regular user DELETE -> 403 Forbidden
    assert (await async_client.delete(f"/api/v1/activities/{act_id}", headers=headers_norm)).status_code == 403

    # Admin user DELETE -> 204 No Content
    assert (await async_client.delete(f"/api/v1/activities/{act_id}", headers=headers_admin)).status_code == 204


@pytest.mark.asyncio
async def test_cross_tenant_activity_attack_prevention(async_client: AsyncClient):
    """
    CRITICAL CROSS-TENANT SECURITY TEST:
    Verify User A cannot GET, PUT, complete, cancel, or DELETE Activity B. Returns 404.
    """
    slug_a = f"act-tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"act-tenant-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Act Tenant A",
        "organization_slug": slug_a,
        "email": "userA@acttenanta.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Act Tenant B",
        "organization_slug": slug_b,
        "email": "userB@acttenantb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create Activity B in Tenant B
    act_b_id = (await async_client.post("/api/v1/activities", json={"activity_type": "task", "title": "Secret B Task"}, headers=headers_b)).json()["id"]

    # User A GET Activity B -> 404
    assert (await async_client.get(f"/api/v1/activities/{act_b_id}", headers=headers_a)).status_code == 404

    # User A PUT Activity B -> 404
    assert (await async_client.put(f"/api/v1/activities/{act_b_id}", json={"title": "Hacked"}, headers=headers_a)).status_code == 404

    # User A complete Activity B -> 404
    assert (await async_client.post(f"/api/v1/activities/{act_b_id}/complete", headers=headers_a)).status_code == 404

    # User A cancel Activity B -> 404
    assert (await async_client.post(f"/api/v1/activities/{act_b_id}/cancel", headers=headers_a)).status_code == 404

    # User A DELETE Activity B -> 404
    assert (await async_client.delete(f"/api/v1/activities/{act_b_id}", headers=headers_a)).status_code == 404
