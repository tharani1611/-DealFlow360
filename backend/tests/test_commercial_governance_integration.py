import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_commercial_governance_pipeline(async_client: AsyncClient):
    """
    REQUIRED END-TO-END TEST SCENARIO:
    Customer -> Deal -> Quotation -> Products -> Pricing -> Margin -> Governance -> Risk -> Approval Required -> Decision -> State Machine -> SENT -> ACCEPTED -> CONVERTED
    """
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Full Governance Pipeline Org",
        "organization_slug": f"full-gov-{uuid.uuid4().hex[:8]}",
        "email": "admin@fullgov.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Setup Customer, Contact, Deal, Products
    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Pipeline Customer"}, headers=headers)).json()["id"]
    deal_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Pipeline Expansion"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Enterprise Cloud Appliance", "sku": "ECA-100", "unit_price": "5000.00", "unit_cost": "2500.00"}, headers=headers)).json()["id"]

    # 2. Setup Governance & Approval Rules
    await async_client.post("/api/v1/discount-governance/policies", json={
        "name": "Standard Max Discount 15%",
        "scope": "organization",
        "max_discount_percent": "15.00"
    }, headers=headers)

    await async_client.post("/api/v1/approvals/rules", json={
        "name": "High Risk / High Discount Approval",
        "min_discount_percent": "20.00"
    }, headers=headers)

    # 3. Create Quotation with 25% discount (exceeds policy & triggers approval rule)
    quot = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "deal_id": deal_id,
        "items": [{
            "product_id": prod_id,
            "quantity": "2.00",
            "unit_price": "5000.00",
            "discount_percent": "25.00",
            "discount_amount": "2500.00"
        }]
    }, headers=headers)).json()
    quot_id = quot["id"]

    # 4. Fetch Integrated Commercial Governance Telemetry
    gov_res = await async_client.get(f"/api/v1/quotations/{quot_id}/governance", headers=headers)
    assert gov_res.status_code == 200
    telemetry = gov_res.json()

    assert telemetry["governance"]["compliant"] is False
    assert telemetry["governance"]["status"] == "OUTSIDE_POLICY"
    assert telemetry["risk"]["risk_level"] in ("HIGH", "CRITICAL")
    assert telemetry["approval"]["status"] == "PENDING"

    # 5. Verify State Machine blocks SENT transition while PENDING
    blocked_tr = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "sent"}, headers=headers)
    assert blocked_tr.status_code == 422

    # 6. Admin approves quotation
    appr_res = await async_client.post(f"/api/v1/approvals/quotations/{quot_id}/decision", json={
        "decision": "APPROVED",
        "note": "Approved by CFO"
    }, headers=headers)
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "APPROVED"

    # 7. Transition pipeline: PRICED -> SENT -> ACCEPTED -> CONVERTED
    await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "priced"}, headers=headers)
    sent_res = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "sent"}, headers=headers)
    assert sent_res.status_code == 200
    assert sent_res.json()["status"] == "sent"

    acc_res = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "accepted"}, headers=headers)
    assert acc_res.status_code == 200
    assert acc_res.json()["status"] == "accepted"

    conv_res = await async_client.post(f"/api/v1/quotations/{quot_id}/transition", json={"target_status": "converted"}, headers=headers)
    assert conv_res.status_code == 200
    assert conv_res.json()["status"] == "converted"
