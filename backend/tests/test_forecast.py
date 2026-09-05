import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_empty_organization_forecast(async_client: AsyncClient):
    """Verifies forecast calculation for an organization with no deals returns zeroed metrics."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Empty Forecast Org",
        "organization_slug": f"emptyorg-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@emptyorg.com",
        "password": "Password123!",
        "full_name": "Empty User"
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    response = await async_client.get("/api/v1/intelligence/forecast", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["open_pipeline"] == "0.00"
    assert data["weighted_pipeline"] == "0.00"
    assert data["forecast_revenue"] == "0.00"
    assert data["committed_revenue"] == "0.00"
    assert data["upside_revenue"] == "0.00"
    assert data["at_risk_revenue"] == "0.00"
    assert data["confidence_score"] >= 0
    assert "confidence_label" in data
    assert isinstance(data["periods"], list)
    assert isinstance(data["deals"], list)


@pytest.mark.asyncio
async def test_forecast_calculations_and_categories(async_client: AsyncClient):
    """Verifies deterministic forecast categories, adjustments, and financial aggregations."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Forecast Calc Org",
        "organization_slug": f"fcalc-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@fcalc.com",
        "password": "Password123!",
        "full_name": "Calc User"
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Create customer & product
    cust_res = await async_client.post("/api/v1/customers", json={"name": "Acme Forecast Corp"}, headers=headers)
    cust_id = cust_res.json()["id"]

    prod_res = await async_client.post("/api/v1/products", json={"name": "Cloud Sub", "sku": "SKU-FC-01", "unit_price": "100000.00"}, headers=headers)
    prod_id = prod_res.json()["id"]

    # Create quotation & accept it
    q_res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": 1}]
    }, headers=headers)
    assert q_res.status_code == 201
    q_id = q_res.json()["id"]
    await async_client.put(f"/api/v1/quotations/{q_id}", json={"status": "sent"}, headers=headers)
    await async_client.put(f"/api/v1/quotations/{q_id}", json={"status": "accepted"}, headers=headers)

    # Deal 1: COMMITTED
    d1_res = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "quotation_id": q_id,
        "title": "Committed Deal",
        "stage": "proposal",
        "value": "100000.00",
        "probability": 80
    }, headers=headers)
    assert d1_res.status_code == 201

    # Deal 2: Early stage / low probability
    d2_res = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "title": "At-Risk Deal",
        "stage": "new",
        "value": "50000.00",
        "probability": 20
    }, headers=headers)
    assert d2_res.status_code == 201

    # Deal 3: Won Deal
    d3_res = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "title": "Won Deal",
        "stage": "proposal",
        "value": "30000.00",
        "probability": 100
    }, headers=headers)
    d3_id = d3_res.json()["id"]
    await async_client.put(f"/api/v1/deals/{d3_id}", json={"stage": "won", "probability": 100}, headers=headers)

    response = await async_client.get("/api/v1/intelligence/forecast", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert Decimal(data["open_pipeline"]) == Decimal("150000.00")
    assert Decimal(data["won_revenue"]) == Decimal("30000.00")
    assert len(data["deals"]) == 2

    # Check deal categories
    d1 = next(d for d in data["deals"] if d["title"] == "Committed Deal")
    d2 = next(d for d in data["deals"] if d["title"] == "At-Risk Deal")

    assert d1["forecast_category"] == "COMMITTED"
    assert d1["adjusted_probability"] >= 70
    assert d2["forecast_category"] == "AT_RISK"


@pytest.mark.asyncio
async def test_tenant_forecast_isolation(async_client: AsyncClient):
    """Confirms Org A cannot see Org B forecast metrics."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Forecast Org A",
        "organization_slug": f"forga-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@orga.com",
        "password": "Password123!",
        "full_name": "Org A User"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    cust_a = await async_client.post("/api/v1/customers", json={"name": "Org A Customer"}, headers=headers_a)
    await async_client.post("/api/v1/deals", json={
        "customer_id": cust_a.json()["id"],
        "title": "Org A Secret Deal",
        "stage": "proposal",
        "value": "77000.00"
    }, headers=headers_a)

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Forecast Org B",
        "organization_slug": f"forgb-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@orgb.com",
        "password": "Password123!",
        "full_name": "Org B User"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    cust_b = await async_client.post("/api/v1/customers", json={"name": "Org B Customer"}, headers=headers_b)
    await async_client.post("/api/v1/deals", json={
        "customer_id": cust_b.json()["id"],
        "title": "Org B Secret Deal",
        "stage": "negotiation",
        "value": "99000.00"
    }, headers=headers_b)

    # Org A request
    res_a = await async_client.get("/api/v1/intelligence/forecast", headers=headers_a)
    assert res_a.status_code == 200
    titles_a = [d["title"] for d in res_a.json()["deals"]]
    assert "Org A Secret Deal" in titles_a
    assert "Org B Secret Deal" not in titles_a

    # Org B request
    res_b = await async_client.get("/api/v1/intelligence/forecast", headers=headers_b)
    assert res_b.status_code == 200
    titles_b = [d["title"] for d in res_b.json()["deals"]]
    assert "Org B Secret Deal" in titles_b
    assert "Org A Secret Deal" not in titles_b


@pytest.mark.asyncio
async def test_unauthenticated_forecast_rejected(async_client: AsyncClient):
    """Verifies unauthenticated GET /api/v1/intelligence/forecast returns 401."""
    res = await async_client.get("/api/v1/intelligence/forecast")
    assert res.status_code == 401
