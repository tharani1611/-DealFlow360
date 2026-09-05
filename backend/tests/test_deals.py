import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_unauthenticated_deal_endpoints_rejected(async_client: AsyncClient):
    """Verify anonymous access to deal endpoints returns 401 Unauthorized."""
    fake_id = str(uuid.uuid4())
    assert (await async_client.get("/api/v1/deals")).status_code == 401
    assert (await async_client.get("/api/v1/deals/pipeline")).status_code == 401
    assert (await async_client.post("/api/v1/deals", json={"title": "Test", "customer_id": fake_id})).status_code == 401
    assert (await async_client.get(f"/api/v1/deals/{fake_id}")).status_code == 401
    assert (await async_client.put(f"/api/v1/deals/{fake_id}", json={"title": "Test"})).status_code == 401
    assert (await async_client.delete(f"/api/v1/deals/{fake_id}")).status_code == 401


@pytest.mark.asyncio
async def test_create_deal_success_and_defaults(async_client: AsyncClient):
    """Verify authenticated user can create a deal with auto-generated deal_number and default stage/probability."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Deal Create Org",
        "organization_slug": f"deal-create-{uuid.uuid4().hex[:8]}",
        "email": "admin@dealcreate.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Customer
    cust_resp = await async_client.post("/api/v1/customers", json={"name": "Acme Deal Corp"}, headers=headers)
    cust_id = cust_resp.json()["id"]

    deal_payload = {
        "customer_id": cust_id,
        "title": "Enterprise Cloud Expansion",
        "description": "Multi-year server expansion project",
        "value": "25000.00",
        "notes": "Target Q4 close"
    }

    resp = await async_client.post("/api/v1/deals", json=deal_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["deal_number"] == "DEAL-000001"
    assert data["title"] == "Enterprise Cloud Expansion"
    assert data["organization_id"] == org_id
    assert data["customer_id"] == cust_id
    assert data["stage"] == "new"
    assert data["status"] == "open"
    assert Decimal(data["value"]) == Decimal("25000.00")
    assert data["probability"] == 10
    assert data["contact_id"] is None
    assert data["quotation_id"] is None


@pytest.mark.asyncio
async def test_deal_number_sequential_per_tenant(async_client: AsyncClient):
    """Verify deal numbers start at DEAL-000001 independently for each organization."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Deal Seq Org A",
        "organization_slug": f"dseq-a-{uuid.uuid4().hex[:8]}",
        "email": "adminA@dseqa.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Deal Seq Org B",
        "organization_slug": f"dseq-b-{uuid.uuid4().hex[:8]}",
        "email": "adminB@dseqb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Cust A"}, headers=headers_a)).json()["id"]
    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()["id"]

    d_a1 = await async_client.post("/api/v1/deals", json={"customer_id": cust_a, "title": "Deal A1"}, headers=headers_a)
    d_a2 = await async_client.post("/api/v1/deals", json={"customer_id": cust_a, "title": "Deal A2"}, headers=headers_a)

    assert d_a1.json()["deal_number"] == "DEAL-000001"
    assert d_a2.json()["deal_number"] == "DEAL-000002"

    d_b1 = await async_client.post("/api/v1/deals", json={"customer_id": cust_b, "title": "Deal B1"}, headers=headers_b)
    assert d_b1.json()["deal_number"] == "DEAL-000001"


@pytest.mark.asyncio
async def test_contact_and_quotation_relationships(async_client: AsyncClient):
    """Verify associating valid contact and quotation belonging to the customer succeeds."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Rel Org",
        "organization_slug": f"rel-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@relorg.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Rel Cust"}, headers=headers)).json()["id"]
    contact_id = (await async_client.post("/api/v1/contacts", json={"customer_id": cust_id, "first_name": "John", "last_name": "Doe"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Rel Prod", "sku": "RP-1", "unit_price": "100.00"}, headers=headers)).json()["id"]
    quot_id = (await async_client.post("/api/v1/quotations", json={"customer_id": cust_id, "items": [{"product_id": prod_id, "quantity": "2"}]}, headers=headers)).json()["id"]

    deal_resp = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "contact_id": contact_id,
        "quotation_id": quot_id,
        "title": "Full Package Deal",
        "value": "200.00"
    }, headers=headers)
    assert deal_resp.status_code == 201
    data = deal_resp.json()
    assert data["customer_id"] == cust_id
    assert data["contact_id"] == contact_id
    assert data["quotation_id"] == quot_id


@pytest.mark.asyncio
async def test_contact_or_quotation_customer_mismatch_rejected(async_client: AsyncClient):
    """Verify associating a contact or quotation belonging to a DIFFERENT customer returns 404 Not Found."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Mismatch Org",
        "organization_slug": f"mismatch-{uuid.uuid4().hex[:8]}",
        "email": "admin@mismatch.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust1_id = (await async_client.post("/api/v1/customers", json={"name": "Customer 1"}, headers=headers)).json()["id"]
    cust2_id = (await async_client.post("/api/v1/customers", json={"name": "Customer 2"}, headers=headers)).json()["id"]

    contact2_id = (await async_client.post("/api/v1/contacts", json={"customer_id": cust2_id, "first_name": "Jane"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "P1", "unit_price": "50.00"}, headers=headers)).json()["id"]
    quot2_id = (await async_client.post("/api/v1/quotations", json={"customer_id": cust2_id, "items": [{"product_id": prod_id, "quantity": "1"}]}, headers=headers)).json()["id"]

    # Try attaching Contact from Cust 2 to Deal for Cust 1 -> 404
    res_contact = await async_client.post("/api/v1/deals", json={
        "customer_id": cust1_id,
        "contact_id": contact2_id,
        "title": "Bad Contact Deal"
    }, headers=headers)
    assert res_contact.status_code == 404

    # Try attaching Quotation from Cust 2 to Deal for Cust 1 -> 404
    res_quot = await async_client.post("/api/v1/deals", json={
        "customer_id": cust1_id,
        "quotation_id": quot2_id,
        "title": "Bad Quotation Deal"
    }, headers=headers)
    assert res_quot.status_code == 404


@pytest.mark.asyncio
async def test_stage_transitions_and_finalization(async_client: AsyncClient):
    """Verify stage transitions, probability updates, lost_reason requirement, and closed deal immutability."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Stage Org",
        "organization_slug": f"stage-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@stageorg.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Stage Cust"}, headers=headers)).json()["id"]
    deal_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Pipeline Deal"}, headers=headers)).json()["id"]

    # new -> qualified
    q_res = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "qualified"}, headers=headers)
    assert q_res.status_code == 200
    assert q_res.json()["stage"] == "qualified"
    assert q_res.json()["probability"] == 25

    # qualified -> proposal
    p_res = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "proposal"}, headers=headers)
    assert p_res.status_code == 200
    assert p_res.json()["stage"] == "proposal"
    assert p_res.json()["probability"] == 50

    # proposal -> negotiation
    n_res = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "negotiation"}, headers=headers)
    assert n_res.status_code == 200
    assert n_res.json()["stage"] == "negotiation"
    assert n_res.json()["probability"] == 75

    # negotiation -> lost WITHOUT lost_reason -> 422 BusinessRuleViolation
    lost_bad = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "lost"}, headers=headers)
    assert lost_bad.status_code == 422

    # negotiation -> lost WITH lost_reason -> 200 OK
    lost_ok = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "lost", "lost_reason": "Competitor gave 50% discount"}, headers=headers)
    assert lost_ok.status_code == 200
    assert lost_ok.json()["stage"] == "lost"
    assert lost_ok.json()["status"] == "lost"
    assert lost_ok.json()["probability"] == 0
    assert lost_ok.json()["lost_reason"] == "Competitor gave 50% discount"

    # Try reopening lost deal (lost -> new) -> 422 BusinessRuleViolation
    reopen_res = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "new"}, headers=headers)
    assert reopen_res.status_code == 422

    # Try modifying content of closed deal -> 422 BusinessRuleViolation
    mod_res = await async_client.put(f"/api/v1/deals/{deal_id}", json={"value": "99999.00"}, headers=headers)
    assert mod_res.status_code == 422


@pytest.mark.asyncio
async def test_won_stage_transition(async_client: AsyncClient):
    """Verify transitioning to 'won' sets status='won' and probability=100."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Won Org",
        "organization_slug": f"won-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@wonorg.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Won Cust"}, headers=headers)).json()["id"]
    deal_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Victorious Deal"}, headers=headers)).json()["id"]

    won_res = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "won"}, headers=headers)
    assert won_res.status_code == 200
    assert won_res.json()["stage"] == "won"
    assert won_res.json()["status"] == "won"
    assert won_res.json()["probability"] == 100


@pytest.mark.asyncio
async def test_pipeline_kanban_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/deals/pipeline returns deals grouped by stage."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Pipeline Org",
        "organization_slug": f"pipe-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@pipeorg.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Pipe Cust"}, headers=headers)).json()["id"]

    d1 = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "New Deal 1"}, headers=headers)).json()["id"]
    d2 = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Qualified Deal 2", "stage": "qualified"}, headers=headers)).json()["id"]

    pipe_res = await async_client.get("/api/v1/deals/pipeline", headers=headers)
    assert pipe_res.status_code == 200
    data = pipe_res.json()["stages"]

    assert "new" in data
    assert "qualified" in data
    assert "proposal" in data
    assert "negotiation" in data
    assert "won" in data
    assert "lost" in data

    assert len(data["new"]) == 1
    assert data["new"][0]["id"] == d1
    assert len(data["qualified"]) == 1
    assert data["qualified"][0]["id"] == d2


@pytest.mark.asyncio
async def test_delete_deal_admin_authorization(async_client: AsyncClient):
    """Verify DELETE deal succeeds for Admin (204) and is forbidden for regular user (403)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Del Deal Org",
        "organization_slug": f"del-deal-{uuid.uuid4().hex[:8]}",
        "email": "admin@deldeal.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular user
    async with AsyncSessionLocal() as session:
        reg_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@deldeal.com",
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

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Del Cust"}, headers=headers_admin)).json()["id"]
    deal_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "To Delete"}, headers=headers_admin)).json()["id"]

    # Regular user DELETE -> 403 Forbidden
    assert (await async_client.delete(f"/api/v1/deals/{deal_id}", headers=headers_norm)).status_code == 403

    # Admin user DELETE -> 204 No Content
    assert (await async_client.delete(f"/api/v1/deals/{deal_id}", headers=headers_admin)).status_code == 204


@pytest.mark.asyncio
async def test_cross_tenant_deal_attack_prevention(async_client: AsyncClient):
    """
    CRITICAL CROSS-TENANT SECURITY TEST:
    1. Creating deal with cross-tenant customer returns 404.
    2. GET, PUT, DELETE cross-tenant deal returns 404.
    """
    slug_a = f"d-tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"d-tenant-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "D Tenant A",
        "organization_slug": slug_a,
        "email": "userA@dtenanta.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "D Tenant B",
        "organization_slug": slug_b,
        "email": "userB@dtenantb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Cust A"}, headers=headers_a)).json()["id"]
    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()["id"]

    # User A tries using Cust B -> 404
    assert (await async_client.post("/api/v1/deals", json={"customer_id": cust_b, "title": "Cross Deal"}, headers=headers_a)).status_code == 404

    # Create valid Deal in Org B
    deal_b_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_b, "title": "Org B Deal"}, headers=headers_b)).json()["id"]

    # User A tries GET Deal B -> 404
    assert (await async_client.get(f"/api/v1/deals/{deal_b_id}", headers=headers_a)).status_code == 404

    # User A tries PUT Deal B -> 404
    assert (await async_client.put(f"/api/v1/deals/{deal_b_id}", json={"title": "Hacked Deal"}, headers=headers_a)).status_code == 404

    # User A tries DELETE Deal B -> 404
    assert (await async_client.delete(f"/api/v1/deals/{deal_b_id}", headers=headers_a)).status_code == 404
