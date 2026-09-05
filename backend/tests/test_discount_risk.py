import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_discount_risk_evaluation_scoring_and_classification(async_client: AsyncClient):
    """Verify commercial risk scoring, blended discount calculation, and classification levels."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Risk Org",
        "organization_slug": f"risk-{uuid.uuid4().hex[:8]}",
        "email": "admin@risk.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Risk Cust"}, headers=headers)).json()["id"]
    # Product cost $800, unit price $1000
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Server Unit", "sku": "SRV-RK", "unit_price": "1000.00", "unit_cost": "800.00"}, headers=headers)).json()["id"]

    # 1. Low risk quotation (0% discount, healthy margin)
    q1 = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "1"}]
    }, headers=headers)).json()["id"]

    risk1 = await async_client.post(f"/api/v1/discount-risk/evaluate?quotation_id={q1}", headers=headers)
    assert risk1.status_code == 200
    res1 = risk1.json()
    assert res1["risk_level"] == "LOW"
    assert res1["has_negative_margin"] is False

    # 2. High / Critical risk quotation (unit_price override $500, cost is $800 -> Negative margin -37.5%)
    q2 = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{
            "product_id": prod_id,
            "quantity": "1",
            "unit_price": "500.00"
        }]
    }, headers=headers)).json()["id"]

    risk2 = await async_client.post(f"/api/v1/discount-risk/evaluate?quotation_id={q2}", headers=headers)
    assert risk2.status_code == 200
    res2 = risk2.json()
    assert res2["risk_level"] == "CRITICAL"
    assert res2["has_negative_margin"] is True
    assert len(res2["risk_factors"]) >= 1
    assert any(rf["code"] == "NEGATIVE_GROSS_MARGIN" for rf in res2["risk_factors"])
