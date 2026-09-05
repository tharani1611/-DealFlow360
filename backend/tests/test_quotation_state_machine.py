import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.models.quotation import Quotation


@pytest.mark.asyncio
async def test_valid_state_transitions_lifecycle(async_client: AsyncClient):
    """Verify full valid quotation lifecycle: draft -> priced -> sent -> accepted -> converted."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "State Lifecycle Org",
        "organization_slug": f"state-lc-{uuid.uuid4().hex[:8]}",
        "email": "admin@statelc.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Lifecycle Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Server Unit", "sku": "SRV-LC", "unit_price": "1000.00"}, headers=headers)).json()["id"]

    # 1. Create -> initial status draft
    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "2"}]
    }, headers=headers)).json()
    quot_id = quot["id"]
    assert quot["status"] == "draft"

    # 2. Draft -> Priced
    tr1 = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "priced",
        "reason": "Calculated tier pricing"
    }, headers=headers)
    assert tr1.status_code == 200
    assert tr1.json()["status"] == "priced"

    # 3. Priced -> Sent
    tr2 = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "sent",
        "reason": "Emailed quotation proposal to client"
    }, headers=headers)
    assert tr2.status_code == 200
    assert tr2.json()["status"] == "sent"

    # 4. Sent -> Accepted
    tr3 = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "accepted",
        "reason": "Client signed quotation proposal"
    }, headers=headers)
    assert tr3.status_code == 200
    assert tr3.json()["status"] == "accepted"

    # 5. Accepted -> Converted
    tr4 = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "converted",
        "reason": "Converted into deal & active contract"
    }, headers=headers)
    assert tr4.status_code == 200
    assert tr4.json()["status"] == "converted"


@pytest.mark.asyncio
async def test_invalid_state_transitions_rejected(async_client: AsyncClient):
    """Verify invalid state transitions are rejected with 422 BusinessRuleViolation."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Invalid State Org",
        "organization_slug": f"inv-state-{uuid.uuid4().hex[:8]}",
        "email": "admin@invstate.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Inv Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Prod", "sku": "INV-P", "unit_price": "100.00"}, headers=headers)).json()["id"]

    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "1"}]
    }, headers=headers)).json()
    quot_id = quot["id"]

    # Direct Draft -> Converted (invalid transition) -> 422
    inv1 = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "converted"
    }, headers=headers)
    assert inv1.status_code == 422

    # Transition to Sent
    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "sent"}, headers=headers)

    # Sent -> Draft (invalid transition) -> 422
    inv2 = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "draft"
    }, headers=headers)
    assert inv2.status_code == 422


@pytest.mark.asyncio
async def test_commercial_field_locking_in_immutable_statuses(async_client: AsyncClient):
    """Verify commercial fields (items, discounts, taxes, customer) cannot be edited when quotation is locked."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Locking Org",
        "organization_slug": f"locking-{uuid.uuid4().hex[:8]}",
        "email": "admin@locking.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Lock Cust"}, headers=headers)).json()["id"]
    prod1 = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "L1", "unit_price": "500.00"}, headers=headers)).json()["id"]
    prod2 = (await async_client.post("/api/v1/products", json={"name": "P2", "sku": "L2", "unit_price": "200.00"}, headers=headers)).json()["id"]

    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod1, "quantity": "1"}]
    }, headers=headers)).json()
    quot_id = quot["id"]

    # Transition to Sent (locked)
    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "sent"}, headers=headers)

    # Attempt PUT items update in Sent status -> 422
    upd_items = await async_client.put(f"/api/v1/quotations/{quot_id}", json={
        "items": [{"product_id": prod2, "quantity": "3"}]
    }, headers=headers)
    assert upd_items.status_code == 422

    # Attempt PUT discount update in Sent status -> 422
    upd_disc = await async_client.put(f"/api/v1/quotations/{quot_id}", json={
        "discount_amount": "50.00"
    }, headers=headers)
    assert upd_disc.status_code == 422


@pytest.mark.asyncio
async def test_requoting_expired_quotation(async_client: AsyncClient):
    """Verify an expired quotation can be reset to draft (re-quoting) and subsequently updated."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Requote Org",
        "organization_slug": f"requote-{uuid.uuid4().hex[:8]}",
        "email": "admin@requote.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Requote Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "RQ1", "unit_price": "100.00"}, headers=headers)).json()["id"]

    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "1"}]
    }, headers=headers)).json()
    quot_id = quot["id"]

    # Draft -> Sent -> Expired
    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "sent"}, headers=headers)
    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "expired"}, headers=headers)

    # Re-quote: Expired -> Draft
    req = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "draft",
        "reason": "Re-quoting expired offer with updated discount"
    }, headers=headers)
    assert req.status_code == 200
    assert req.json()["status"] == "draft"

    # Now back in draft, item edits are allowed again
    edit_res = await async_client.put(f"/api/v1/quotations/{quot_id}", json={
        "discount_amount": "10.00"
    }, headers=headers)
    assert edit_res.status_code == 200
    assert Decimal(edit_res.json()["discount_amount"]) == Decimal("10.00")


@pytest.mark.asyncio
async def test_lazy_expiration_check_on_fetch(async_client: AsyncClient):
    """Verify quotation with status 'sent' and past valid_until auto-expires upon fetch."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Lazy Exp Org",
        "organization_slug": f"lazy-exp-{uuid.uuid4().hex[:8]}",
        "email": "admin@lazyexp.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Lazy Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "LZ1", "unit_price": "100.00"}, headers=headers)).json()["id"]

    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "valid_until": future_date,
        "items": [{"product_id": prod_id, "quantity": "1"}]
    }, headers=headers)).json()
    quot_id = quot["id"]

    # Transition to sent
    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "sent"}, headers=headers)

    # Directly update DB valid_until to past date to simulate time passing while sent
    async with AsyncSessionLocal() as session:
        db_q = await session.get(Quotation, uuid.UUID(quot_id))
        db_q.valid_until = datetime.now(timezone.utc) - timedelta(days=2)
        await session.commit()

    # GET quotation details -> should trigger lazy expiration check to 'expired'
    fetch_res = await async_client.get(f"/api/v1/quotations/{quot_id}", headers=headers)
    assert fetch_res.status_code == 200
    assert fetch_res.json()["status"] == "expired"


@pytest.mark.asyncio
async def test_state_history_audit_trail(async_client: AsyncClient):
    """Verify state history audit log endpoint records chronological events."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Audit Trail Org",
        "organization_slug": f"audit-{uuid.uuid4().hex[:8]}",
        "email": "admin@audit.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Audit Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "AU1", "unit_price": "100.00"}, headers=headers)).json()["id"]

    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "1"}]
    }, headers=headers)).json()
    quot_id = quot["id"]

    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "priced",
        "reason": "Calculated volume price"
    }, headers=headers)

    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={
        "target_status": "sent",
        "reason": "Sent email proposal"
    }, headers=headers)

    # Fetch history endpoint
    hist_res = await async_client.get(f"/api/v1/quotations/{quot_id}/history", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()

    assert len(history) == 3
    # Most recent first
    assert history[0]["from_status"] == "priced"
    assert history[0]["to_status"] == "sent"
    assert history[0]["reason"] == "Sent email proposal"

    assert history[1]["from_status"] == "draft"
    assert history[1]["to_status"] == "priced"
    assert history[1]["reason"] == "Calculated volume price"

    assert history[2]["from_status"] is None
    assert history[2]["to_status"] == "draft"
    assert history[2]["reason"] == "Initial draft created"


@pytest.mark.asyncio
async def test_cross_tenant_state_transition_prevention(async_client: AsyncClient):
    """Verify cross-tenant attempt to transition or view state history of another organization's quotation returns 404."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "CT State Org A",
        "organization_slug": f"ct-state-a-{uuid.uuid4().hex[:8]}",
        "email": "userA@ctstatea.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "CT State Org B",
        "organization_slug": f"ct-state-b-{uuid.uuid4().hex[:8]}",
        "email": "userB@ctstateb.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()["id"]
    prod_b = (await async_client.post("/api/v1/products", json={"name": "Prod B", "sku": "PB", "unit_price": "100.00"}, headers=headers_b)).json()["id"]
    quot_b = (await async_client.post("/api/v1/quotations", json={"customer_id": cust_b, "items": [{"product_id": prod_b, "quantity": "1"}]}, headers=headers_b)).json()["id"]

    # User A attempts transition on Quotation B -> 404
    tr_res = await async_client.post(f"/api/v1/quotations/{quot_b}/transition", json={"target_status": "sent"}, headers=headers_a)
    assert tr_res.status_code == 404

    # User A attempts GET history of Quotation B -> 404
    hist_res = await async_client.get(f"/api/v1/quotations/{quot_b}/history", headers=headers_a)
    assert hist_res.status_code == 404
