import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_co_negotiator_simulation_engine(async_client: AsyncClient):
    """Verify AI Co-Negotiator scenario simulation engine returns 3 distinct optimal counter-offer strategies."""
    # 1. Register organization & user
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "CoNegotiator Test Org",
        "organization_slug": f"coneg-{uuid.uuid4().hex[:8]}",
        "email": "sales@coneg.com",
        "password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Customer & Product
    cust_resp = await async_client.post("/api/v1/customers", json={"name": "Coneg Customer"}, headers=headers)
    cust_id = cust_resp.json()["id"]

    prod_resp = await async_client.post("/api/v1/products", json={
        "name": "Enterprise Workstation",
        "sku": f"WS-{uuid.uuid4().hex[:4]}",
        "unit_price": "2000.00"
    }, headers=headers)
    prod_id = prod_resp.json()["id"]

    # 3. Create Quotation
    quote_resp = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "discount_percent": "5.0",
        "items": [{"product_id": prod_id, "quantity": 10, "unit_price": "2000.00"}]
    }, headers=headers)
    assert quote_resp.status_code == 201
    quote_id = quote_resp.json()["id"]

    # 4. Trigger AI Co-Negotiator Simulation
    sim_resp = await async_client.post(f"/api/v1/quotations/{quote_id}/simulate-counter-offer", json={
        "requested_discount_percent": 15.0,
        "target_win_probability": 80
    }, headers=headers)

    assert sim_resp.status_code == 200
    data = sim_resp.json()

    assert data["quotation_id"] == quote_id
    assert data["simulated_scenarios_count"] == 120
    assert len(data["recommended_scenarios"]) == 3

    strategies = [s["strategy_type"] for s in data["recommended_scenarios"]]
    assert "BALANCED" in strategies
    assert "VOLUME_INCENTIVE" in strategies
    assert "VALUE_ADD_SWAP" in strategies

    for s in data["recommended_scenarios"]:
        assert s["simulated_win_probability"] >= 50
        assert float(s["projected_gross_margin_percent"]) > 0
        assert len(s["offered_perks"]) >= 1
        assert len(s["counter_proposal_script"]) > 10
