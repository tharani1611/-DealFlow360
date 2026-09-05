import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_positive_and_health_margin(async_client: AsyncClient):
    """Verify positive margin calculation and HEALTHY status classification."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Positive Margin Org",
        "organization_slug": f"pos-margin-{uuid.uuid4().hex[:8]}",
        "email": "admin@posmargin.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod = (await async_client.post("/api/v1/products", json={
        "name": "High Margin Software",
        "sku": "SW-HIGH-01",
        "unit_price": "1000.00",
        "unit_cost": "600.00"
    }, headers=headers)).json()
    prod_id = prod["id"]

    res = await async_client.post("/api/v1/margins/calculate", json={
        "currency": "USD",
        "items": [{"product_id": prod_id, "quantity": "50.00"}]
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["total_revenue"]) == Decimal("50000.00")  # 50 * 1000
    assert Decimal(data["total_cost"]) == Decimal("30000.00")     # 50 * 600
    assert Decimal(data["gross_margin"]) == Decimal("20000.00")    # 50000 - 30000
    assert Decimal(data["margin_percent"]) == Decimal("40.00")     # (20000 / 50000) * 100
    assert data["health_status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_negative_margin_and_classification(async_client: AsyncClient):
    """Verify negative margin support (selling price < cost) and NEGATIVE health status."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Negative Margin Org",
        "organization_slug": f"neg-margin-{uuid.uuid4().hex[:8]}",
        "email": "admin@negmargin.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod = (await async_client.post("/api/v1/products", json={
        "name": "Loss Leader Hardware",
        "sku": "HW-LOSS-01",
        "unit_price": "800.00",
        "unit_cost": "1000.00"
    }, headers=headers)).json()
    prod_id = prod["id"]

    res = await async_client.post("/api/v1/margins/calculate", json={
        "items": [{"product_id": prod_id, "quantity": "10.00"}]
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["total_revenue"]) == Decimal("8000.00")
    assert Decimal(data["total_cost"]) == Decimal("10000.00")
    assert Decimal(data["gross_margin"]) == Decimal("-2000.00")
    assert Decimal(data["margin_percent"]) == Decimal("-25.00")
    assert data["health_status"] == "NEGATIVE"


@pytest.mark.asyncio
async def test_zero_revenue_guard(async_client: AsyncClient):
    """Verify 0.00 selling price does not cause ZeroDivisionError."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Zero Rev Org",
        "organization_slug": f"zero-rev-{uuid.uuid4().hex[:8]}",
        "email": "admin@zerorev.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod_id = (await async_client.post("/api/v1/products", json={
        "name": "Free Sample",
        "sku": "FREE-01",
        "unit_price": "0.00",
        "unit_cost": "10.00"
    }, headers=headers)).json()["id"]

    res = await async_client.post("/api/v1/margins/calculate", json={
        "items": [{"product_id": prod_id, "quantity": "1.00"}]
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["total_revenue"]) == Decimal("0.00")
    assert Decimal(data["total_cost"]) == Decimal("10.00")
    assert Decimal(data["gross_margin"]) == Decimal("-10.00")
    assert Decimal(data["margin_percent"]) == Decimal("-100.00")
    assert data["health_status"] == "NEGATIVE"


@pytest.mark.asyncio
async def test_multi_item_weighted_quotation_margin(async_client: AsyncClient):
    """Verify multi-item quotation margin aggregates using weighted total margin rather than simple average."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Weighted Margin Org",
        "organization_slug": f"weight-m-{uuid.uuid4().hex[:8]}",
        "email": "admin@weightm.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod_a = (await async_client.post("/api/v1/products", json={"name": "Item A", "sku": "A-01", "unit_price": "100.00", "unit_cost": "60.00"}, headers=headers)).json()["id"]
    prod_b = (await async_client.post("/api/v1/products", json={"name": "Item B", "sku": "B-01", "unit_price": "50.00", "unit_cost": "20.00"}, headers=headers)).json()["id"]

    # Item A: Qty 100 -> Rev 10,000, Cost 6,000, Margin 4,000 (40.00%)
    # Item B: Qty 100 -> Rev 5,000, Cost 2,000, Margin 3,000 (60.00%)
    # Total: Rev 15,000, Cost 8,000, Margin 7,000 -> 7000 / 15000 = 46.67%
    res = await async_client.post("/api/v1/margins/calculate", json={
        "items": [
            {"product_id": prod_a, "quantity": "100.00"},
            {"product_id": prod_b, "quantity": "100.00"}
        ]
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["total_revenue"]) == Decimal("15000.00")
    assert Decimal(data["total_cost"]) == Decimal("8000.00")
    assert Decimal(data["gross_margin"]) == Decimal("7000.00")
    assert Decimal(data["margin_percent"]) == Decimal("46.67")
    assert data["health_status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_margin_uses_phase_20_pricing_and_cost_snapshots(async_client: AsyncClient):
    """Verify Margin engine consumes Phase 20 final selling prices and snapshots unit_cost on Quotation creation."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Margin Phase 20 Integration Org",
        "organization_slug": f"m-p20-{uuid.uuid4().hex[:8]}",
        "email": "admin@mp20.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Big Enterprise"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Enterprise Suite", "sku": "ENT-99", "unit_price": "1000.00", "unit_cost": "500.00"}, headers=headers)).json()["id"]

    # Phase 20 Volume Tier Rule: Qty 50+ -> 800.00 selling price
    await async_client.post("/api/v1/pricing/rules", json={
        "name": "50+ Volume Tier",
        "rule_type": "volume",
        "product_id": prod_id,
        "min_quantity": "50.00",
        "price_type": "override_price",
        "value": "800.00",
        "priority": 10
    }, headers=headers)

    # 1. Preview calculation -> Selling price 800, Cost 500, Margin 300 (37.50%)
    res_prev = await async_client.post("/api/v1/margins/calculate", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "50.00"}]
    }, headers=headers)
    assert res_prev.status_code == 200
    p_data = res_prev.json()
    assert Decimal(p_data["items"][0]["unit_selling_price"]) == Decimal("800.00")
    assert Decimal(p_data["items"][0]["unit_cost"]) == Decimal("500.00")
    assert Decimal(p_data["margin_percent"]) == Decimal("37.50")

    # 2. Create Quotation -> unit_cost and unit_price are snapshotted onto QuotationItem
    quot_res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "title": "50 Unit License Deal",
        "items": [{"product_id": prod_id, "quantity": "50.00"}]
    }, headers=headers)
    assert quot_res.status_code == 201
    q_data = quot_res.json()
    quot_id = q_data["id"]

    # 3. GET /margins/quotations/{id} -> Returns historical margin
    res_q_margin = await async_client.get(f"/api/v1/margins/quotations/{quot_id}", headers=headers)
    assert res_q_margin.status_code == 200
    qm_data = res_q_margin.json()
    assert Decimal(qm_data["total_revenue"]) == Decimal("40000.00")  # 50 * 800
    assert Decimal(qm_data["total_cost"]) == Decimal("25000.00")     # 50 * 500
    assert Decimal(qm_data["gross_margin"]) == Decimal("15000.00")
    assert Decimal(qm_data["margin_percent"]) == Decimal("37.50")

    # 4. Modify Product base cost to 700.00
    await async_client.put(f"/api/v1/products/{prod_id}", json={"unit_cost": "700.00"}, headers=headers)

    # Re-fetch quotation margin -> Historical cost remains snapshotted at 500.00!
    res_q_margin_after = await async_client.get(f"/api/v1/margins/quotations/{quot_id}", headers=headers)
    assert Decimal(res_q_margin_after.json()["total_cost"]) == Decimal("25000.00")
    assert Decimal(res_q_margin_after.json()["margin_percent"]) == Decimal("37.50")


@pytest.mark.asyncio
async def test_manual_price_override_margin(async_client: AsyncClient):
    """Verify margin calculation uses manual unit price override when provided."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Manual Override Margin Org",
        "organization_slug": f"man-margin-{uuid.uuid4().hex[:8]}",
        "email": "admin@manmargin.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod_id = (await async_client.post("/api/v1/products", json={"name": "Custom Server", "sku": "SRV-CUST-01", "unit_price": "1000.00", "unit_cost": "600.00"}, headers=headers)).json()["id"]

    # Manual unit_price override 850.00
    # Revenue: 850, Cost: 600, Gross Margin: 250, Margin %: (250 / 850) * 100 = 29.41% (CAUTION)
    res = await async_client.post("/api/v1/margins/calculate", json={
        "items": [{"product_id": prod_id, "quantity": "1.00", "manual_unit_price": "850.00"}]
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["total_revenue"]) == Decimal("850.00")
    assert Decimal(data["total_cost"]) == Decimal("600.00")
    assert Decimal(data["gross_margin"]) == Decimal("250.00")
    assert Decimal(data["margin_percent"]) == Decimal("29.41")
    assert data["health_status"] == "CAUTION"


@pytest.mark.asyncio
async def test_cross_tenant_margin_isolation(async_client: AsyncClient):
    """Verify Organization B cannot access Organization A quotation or deal margins."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org A Margin Tenant",
        "organization_slug": f"margin-a-{uuid.uuid4().hex[:8]}",
        "email": "adminA@mtenant.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org B Margin Tenant",
        "organization_slug": f"margin-b-{uuid.uuid4().hex[:8]}",
        "email": "adminB@mtenant.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Cust A"}, headers=headers_a)).json()["id"]
    prod_a = (await async_client.post("/api/v1/products", json={"name": "Prod A", "sku": "PA", "unit_price": "100.00", "unit_cost": "50.00"}, headers=headers_a)).json()["id"]

    quot_a = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_a,
        "items": [{"product_id": prod_a, "quantity": "10.00"}]
    }, headers=headers_a)).json()
    quot_id_a = quot_a["id"]

    # User B attempts to access Org A quotation margin -> 404
    res = await async_client.get(f"/api/v1/margins/quotations/{quot_id_a}", headers=headers_b)
    assert res.status_code == 404
