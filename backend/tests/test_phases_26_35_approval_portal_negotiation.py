import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient

from app.core.database import AsyncSessionLocal
from app.models.portal_user import PortalUser
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_phases_26_35_full_approval_portal_negotiation_flow(async_client: AsyncClient):
    """
    Comprehensive test suite covering Original Phases 26-35:
    - Multi-step approval & audit logging
    - Customer portal authentication & strict isolation
    - Line-level comments with internal vs client visibility
    - Change requests & counter-discount application with decimal math
    - Automatic re-approval invalidation and version snapshots
    """
    # 1. Register organization and admin user
    org_slug = f"pneg-{uuid.uuid4().hex[:8]}"
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Portal Neg Org",
        "organization_slug": org_slug,
        "email": "sales@pnegorg.com",
        "password": "Password123!",
        "full_name": "Sales Rep"
    })
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    internal_token = auth_data["access_token"]
    internal_headers = {"Authorization": f"Bearer {internal_token}"}

    # Fetch user/org info
    user_me = (await async_client.get("/api/v1/auth/me", headers=internal_headers)).json()
    org_id = uuid.UUID(user_me["organization_id"])

    # 2. Create Customer A and Product
    cust_res = await async_client.post("/api/v1/customers", json={"name": "Acme Corp"}, headers=internal_headers)
    assert cust_res.status_code == 201
    cust_a_id = uuid.UUID(cust_res.json()["id"])

    cust_b_res = await async_client.post("/api/v1/customers", json={"name": "Beta LLC"}, headers=internal_headers)
    cust_b_id = uuid.UUID(cust_b_res.json()["id"])

    prod_res = await async_client.post("/api/v1/products", json={
        "name": "Enterprise Server",
        "sku": "SRV-100",
        "unit_price": "5000.00",
        "unit_cost": "3000.00"
    }, headers=internal_headers)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 3. Create Portal User for Customer A directly in DB
    email_a = f"john-{uuid.uuid4().hex[:6]}@acmecorp.com"
    email_b = f"sarah-{uuid.uuid4().hex[:6]}@betallc.com"
    async with AsyncSessionLocal() as session:
        portal_user_a = PortalUser(
            organization_id=org_id,
            customer_id=cust_a_id,
            email=email_a,
            hashed_password=hash_password("PortalPass123!"),
            full_name="John Acme",
            is_active=True
        )
        portal_user_b = PortalUser(
            organization_id=org_id,
            customer_id=cust_b_id,
            email=email_b,
            hashed_password=hash_password("PortalPass123!"),
            full_name="Sarah Beta",
            is_active=True
        )
        session.add_all([portal_user_a, portal_user_b])
        await session.commit()

    # 4. Portal Login for User A
    p_login_res = await async_client.post("/api/v1/portal/auth/login", json={
        "email": email_a,
        "password": "PortalPass123!"
    })
    assert p_login_res.status_code == 200
    portal_token_a = p_login_res.json()["access_token"]
    portal_headers_a = {"Authorization": f"Bearer {portal_token_a}"}

    # Portal Login for User B
    p_login_b = await async_client.post("/api/v1/portal/auth/login", json={
        "email": email_b,
        "password": "PortalPass123!"
    })
    assert p_login_b.status_code == 200
    portal_token_b = p_login_b.json()["access_token"]
    portal_headers_b = {"Authorization": f"Bearer {portal_token_b}"}

    # Test /portal/auth/me
    p_me = await async_client.get("/api/v1/portal/auth/me", headers=portal_headers_a)
    assert p_me.status_code == 200
    assert p_me.json()["email"] == email_a

    # 5. Create Approval Rule
    rule_res = await async_client.post("/api/v1/approvals/rules", json={
        "name": "Discounts > 10% Need Approval",
        "min_discount_percent": "10.00",
        "priority": 1
    }, headers=internal_headers)
    assert rule_res.status_code == 201

    # 6. Create Quotation for Customer A with 15% discount
    q_create = await async_client.post("/api/v1/quotations", json={
        "customer_id": str(cust_a_id),
        "items": [{
            "product_id": prod_id,
            "quantity": "2",
            "unit_price": "5000.00",
            "discount_percent": "15.00",
            "discount_amount": "1500.00"
        }]
    }, headers=internal_headers)
    assert q_create.status_code == 201
    q_data = q_create.json()
    q_id = q_data["id"]
    item_id = q_data["items"][0]["id"]

    # Evaluate commercial governance to trigger approval rule check
    gov_eval = await async_client.get(f"/api/v1/quotations/{q_id}/governance", headers=internal_headers)
    assert gov_eval.status_code == 200
    assert gov_eval.json()["approval"]["status"] == "PENDING"

    # Verify audit logs created for submission
    logs_res = await async_client.get(f"/api/v1/quotations/{q_id}/audit-logs", headers=internal_headers)
    assert logs_res.status_code == 200
    assert len(logs_res.json()) >= 1

    # 7. Attempt to send quotation before approval -> should fail
    send_err = await async_client.post(f"/api/v1/quotations/{q_id}/transition", json={"target_status": "sent"}, headers=internal_headers)
    assert send_err.status_code == 422

    # Approve quotation from internal admin user
    appr_dec = await async_client.post(f"/api/v1/approvals/quotations/{q_id}/decision", json={
        "decision": "APPROVED",
        "note": "Approved by VP"
    }, headers=internal_headers)
    assert appr_dec.status_code == 200, f"Approval decision failed: {appr_dec.text}"
    assert appr_dec.json()["status"] == "APPROVED"

    # Transition to sent
    send_ok = await async_client.post(f"/api/v1/quotations/{q_id}/transition", json={"target_status": "sent"}, headers=internal_headers)
    print("SEND_OK STATUS:", send_ok.status_code, send_ok.text)
    assert send_ok.status_code == 200, f"Transition to sent failed: {send_ok.text}"
    assert send_ok.json()["status"] == "sent"

    # 8. Portal User A views quotation
    p_q_detail = await async_client.get(f"/api/v1/portal/quotations/{q_id}", headers=portal_headers_a)
    assert p_q_detail.status_code == 200
    detail_json = p_q_detail.json()
    assert detail_json["quotation_number"] == q_data["quotation_number"]
    # Ensure internal cost / margin fields NOT present in response schema
    assert "unit_cost" not in detail_json["items"][0]
    assert "gross_margin" not in detail_json

    # 9. Portal User B attempts to access Quotation A -> STRICT CUSTOMER ISOLATION 404
    p_q_b = await async_client.get(f"/api/v1/portal/quotations/{q_id}", headers=portal_headers_b)
    assert p_q_b.status_code == 404

    # 10. Line Comments Flow
    # Internal user posts internal-only comment
    c1 = await async_client.post(f"/api/v1/quotations/{q_id}/comments", json={
        "quotation_item_id": item_id,
        "comment_text": "Internal cost note: Margin is thin",
        "is_internal_only": True
    }, headers=internal_headers)
    assert c1.status_code == 201

    # Internal user posts public comment
    c2 = await async_client.post(f"/api/v1/quotations/{q_id}/comments", json={
        "quotation_item_id": item_id,
        "comment_text": "Includes 3 year warranty",
        "is_internal_only": False
    }, headers=internal_headers)
    assert c2.status_code == 201

    # Portal user views comments -> should only see 1 public comment
    p_comments = await async_client.get(f"/api/v1/portal/quotations/{q_id}/comments", headers=portal_headers_a)
    assert p_comments.status_code == 200
    assert len(p_comments.json()) == 1
    assert p_comments.json()[0]["comment_text"] == "Includes 3 year warranty"

    # Portal user posts a comment
    p_c3 = await async_client.post(f"/api/v1/portal/quotations/{q_id}/comments", json={
        "quotation_item_id": item_id,
        "comment_text": "Can we get 20% discount if we order 5 units?"
    }, headers=portal_headers_a)
    assert p_c3.status_code == 201

    # Internal user views comments -> sees all 3 comments
    int_comments = await async_client.get(f"/api/v1/quotations/{q_id}/comments", headers=internal_headers)
    assert int_comments.status_code == 200
    assert len(int_comments.json()) == 3

    # 11. Change Request / Counter Discount Flow from Portal
    cr_res = await async_client.post(f"/api/v1/portal/quotations/{q_id}/change-requests", json={
        "quotation_item_id": item_id,
        "change_type": "counter_discount",
        "requested_discount_percent": "20.00",
        "request_details": "Requesting 20% discount for enterprise bulk order"
    }, headers=portal_headers_a)
    assert cr_res.status_code == 201
    cr_id = cr_res.json()["id"]

    # Internal user lists and reviews change request
    crs = await async_client.get(f"/api/v1/quotations/{q_id}/change-requests", headers=internal_headers)
    assert len(crs.json()) == 1

    rev_res = await async_client.post(f"/api/v1/quotations/{q_id}/change-requests/{cr_id}/review", json={
        "status": "ACCEPTED",
        "response_note": "Agreed to 20% counter discount"
    }, headers=internal_headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "ACCEPTED"

    # 12. Apply Counter Discount
    cd_res = await async_client.post(f"/api/v1/quotations/{q_id}/counter-discount", json={
        "quotation_item_id": item_id,
        "requested_discount_percent": "20.00",
        "change_reason": "Customer counter-offer accepted"
    }, headers=internal_headers)
    assert cd_res.status_code == 200
    updated_q = cd_res.json()
    assert updated_q["items"][0]["discount_percent"] == 20.0 or updated_q["items"][0]["discount_percent"] == "20.00"

    # Verify Version Snapshots created
    ver_res = await async_client.get(f"/api/v1/quotations/{q_id}/versions", headers=internal_headers)
    assert ver_res.status_code == 200
    assert len(ver_res.json()) >= 2

    # Verify Automatic Approval Invalidation occurred
    inval_logs = await async_client.get(f"/api/v1/quotations/{q_id}/audit-logs", headers=internal_headers)
    assert any(log["event_type"] == "APPROVAL_INVALIDATED" for log in inval_logs.json())

    # Re-evaluate governance to move approval from INVALIDATED to PENDING for new 20% discount
    await async_client.get(f"/api/v1/quotations/{q_id}/governance", headers=internal_headers)

    # Re-approve and re-send quotation
    appr_res2 = await async_client.post(f"/api/v1/approvals/quotations/{q_id}/decision", json={
        "decision": "APPROVED",
        "note": "Re-approved for 20% discount"
    }, headers=internal_headers)
    assert appr_res2.status_code == 200

    send_res2 = await async_client.post(f"/api/v1/quotations/{q_id}/transition", json={"target_status": "sent"}, headers=internal_headers)
    assert send_res2.status_code == 200

    # 13. Portal User Accepts Quotation
    acc_res = await async_client.post(f"/api/v1/portal/quotations/{q_id}/accept", json={
        "reason": "Accepted updated proposal"
    }, headers=portal_headers_a)
    assert acc_res.status_code == 200
    assert acc_res.json()["status"] == "accepted"
