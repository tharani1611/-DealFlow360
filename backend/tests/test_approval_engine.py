import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_approval_rule_crud_and_evaluation(async_client: AsyncClient):
    """Verify approval rule CRUD, automatic evaluation triggering PENDING approval, and approval/rejection decisions."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Appr Rule Org",
        "organization_slug": f"appr-rule-{uuid.uuid4().hex[:8]}",
        "email": "admin@apprrule.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Approval Rule: min_discount_percent = 15.00%
    rule_res = await async_client.post("/api/v1/approvals/rules", json={
        "name": "Discounts >= 15% Require Admin Approval",
        "min_discount_percent": "15.00",
        "priority": 10
    }, headers=headers)
    assert rule_res.status_code == 201
    rule_id = rule_res.json()["id"]

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Appr Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "AP1", "unit_price": "1000.00"}, headers=headers)).json()["id"]

    # 2. Create Quotation with 20% discount (triggers approval rule)
    q = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{
            "product_id": prod_id,
            "quantity": "1",
            "unit_price": "1000.00",
            "discount_percent": "20.00",
            "discount_amount": "200.00"
        }]
    }, headers=headers)).json()
    q_id = q["id"]

    # Fetch commercial governance summary -> status PENDING
    gov_sum = await async_client.get(f"/api/v1/quotations/{q_id}/governance", headers=headers)
    assert gov_sum.status_code == 200
    assert gov_sum.json()["approval"]["status"] == "PENDING"

    # 3. Attempt transitioning quotation to SENT while approval is PENDING -> rejected with 422
    sent_attempt = await async_client.post(f"/api/v1/quotations/{q_id}/transition", json={
        "target_status": "sent"
    }, headers=headers)
    assert sent_attempt.status_code == 422

    # 4. Submit approval decision: APPROVED
    dec_res = await async_client.post(f"/api/v1/approvals/quotations/{q_id}/decision", json={
        "decision": "APPROVED",
        "note": "Approved by VP of Sales for key customer account"
    }, headers=headers)
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == "APPROVED"

    # 5. Now transition to SENT succeeds!
    sent_ok = await async_client.post(f"/api/v1/quotations/{q_id}/transition", json={
        "target_status": "sent"
    }, headers=headers)
    assert sent_ok.status_code == 200
    assert sent_ok.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_commercial_edit_invalidates_existing_approval(async_client: AsyncClient):
    """Verify modifying commercial fields on an APPROVED quotation invalidates approval status."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Inval Appr Org",
        "organization_slug": f"inval-appr-{uuid.uuid4().hex[:8]}",
        "email": "admin@invalappr.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await async_client.post("/api/v1/approvals/rules", json={
        "name": "High Discount Approval",
        "min_discount_percent": "10.00"
    }, headers=headers)

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Inval Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "P1", "sku": "IV1", "unit_price": "1000.00"}, headers=headers)).json()["id"]

    q_id = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{
            "product_id": prod_id,
            "quantity": "1",
            "unit_price": "1000.00",
            "discount_percent": "15.00",
            "discount_amount": "150.00"
        }]
    }, headers=headers)).json()["id"]

    # Evaluate & Approve
    await async_client.get(f"/api/v1/quotations/{q_id}/governance", headers=headers)
    await async_client.post(f"/api/v1/approvals/quotations/{q_id}/decision", json={"decision": "APPROVED"}, headers=headers)

    # Verify approved
    chk1 = await async_client.get(f"/api/v1/quotations/{q_id}/governance", headers=headers)
    assert chk1.json()["approval"]["status"] == "APPROVED"

    # User modifies discount amount to 200.00
    await async_client.put(f"/api/v1/quotations/{q_id}", json={"discount_amount": "200.00"}, headers=headers)

    # Verify approval status is INVALIDATED!
    chk2 = await async_client.get(f"/api/v1/quotations/{q_id}/governance", headers=headers)
    assert chk2.json()["approval"]["status"] == "INVALIDATED" or chk2.json()["approval"]["status"] == "PENDING"
