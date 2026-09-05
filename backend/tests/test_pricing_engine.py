import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_base_product_price(async_client: AsyncClient):
    """Verify fallback to Base Product Price when no pricing rules exist."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Base Price Org",
        "organization_slug": f"base-price-{uuid.uuid4().hex[:8]}",
        "email": "admin@baseprice.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod = (await async_client.post("/api/v1/products", json={"name": "Widget Standard", "sku": "WDG-STD-01", "unit_price": "1000.00"}, headers=headers)).json()
    prod_id = prod["id"]

    # Calculate pricing preview
    res = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_id,
        "quantity": "5.00"
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["base_price"]) == Decimal("1000.00")
    assert Decimal(data["final_unit_price"]) == Decimal("1000.00")
    assert data["pricing_source"] == "BASE_PRODUCT_PRICE"
    assert "Base product price applied" in data["explanation"]


@pytest.mark.asyncio
async def test_volume_tier_thresholds(async_client: AsyncClient):
    """Verify volume pricing tiers and boundary conditions (qty = 9, 10, 49, 50)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Volume Tier Org",
        "organization_slug": f"vol-tier-{uuid.uuid4().hex[:8]}",
        "email": "admin@voltier.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod_id = (await async_client.post("/api/v1/products", json={"name": "Bulk Cable", "sku": "CBL-100", "unit_price": "1000.00"}, headers=headers)).json()["id"]

    # Create Tier 1: Qty 10-49 -> 950.00 (priority 20)
    await async_client.post("/api/v1/pricing/rules", json={
        "name": "Volume 10-49 Tier",
        "rule_type": "volume",
        "product_id": prod_id,
        "min_quantity": "10.00",
        "max_quantity": "49.00",
        "price_type": "override_price",
        "value": "950.00",
        "priority": 20
    }, headers=headers)

    # Create Tier 2: Qty 50+ -> 900.00 (priority 20)
    await async_client.post("/api/v1/pricing/rules", json={
        "name": "Volume 50+ Tier",
        "rule_type": "volume",
        "product_id": prod_id,
        "min_quantity": "50.00",
        "price_type": "override_price",
        "value": "900.00",
        "priority": 20
    }, headers=headers)

    # Test Qty 9 -> Base Price 1000.00
    res9 = await async_client.post("/api/v1/pricing/calculate", json={"product_id": prod_id, "quantity": "9.00"}, headers=headers)
    assert res9.json()["pricing_source"] == "BASE_PRODUCT_PRICE"
    assert Decimal(res9.json()["final_unit_price"]) == Decimal("1000.00")

    # Test Qty 10 -> Volume Tier 950.00
    res10 = await async_client.post("/api/v1/pricing/calculate", json={"product_id": prod_id, "quantity": "10.00"}, headers=headers)
    assert res10.json()["pricing_source"] == "VOLUME"
    assert Decimal(res10.json()["final_unit_price"]) == Decimal("950.00")

    # Test Qty 49 -> Volume Tier 950.00
    res49 = await async_client.post("/api/v1/pricing/calculate", json={"product_id": prod_id, "quantity": "49.00"}, headers=headers)
    assert res49.json()["pricing_source"] == "VOLUME"
    assert Decimal(res49.json()["final_unit_price"]) == Decimal("950.00")

    # Test Qty 50 -> Volume Tier 900.00
    res50 = await async_client.post("/api/v1/pricing/calculate", json={"product_id": prod_id, "quantity": "50.00"}, headers=headers)
    assert res50.json()["pricing_source"] == "VOLUME"
    assert Decimal(res50.json()["final_unit_price"]) == Decimal("900.00")


@pytest.mark.asyncio
async def test_customer_and_contract_pricing(async_client: AsyncClient):
    """Verify Customer and Contract pricing rule application and date validity."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Contract Pricing Org",
        "organization_slug": f"contract-p-{uuid.uuid4().hex[:8]}",
        "email": "admin@contractp.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "VIP Enterprise Client"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Enterprise Server", "sku": "SRV-ENT-01", "unit_price": "5000.00"}, headers=headers)).json()["id"]

    # Active Contract Rule: 4000.00 for VIP Client
    now = datetime.now(timezone.utc)
    valid_from = (now - timedelta(days=5)).isoformat()
    valid_until = (now + timedelta(days=30)).isoformat()

    await async_client.post("/api/v1/pricing/rules", json={
        "name": "VIP Enterprise Master Agreement",
        "rule_type": "contract",
        "product_id": prod_id,
        "customer_id": cust_id,
        "min_quantity": "1.00",
        "price_type": "override_price",
        "value": "4000.00",
        "priority": 1,
        "valid_from": valid_from,
        "valid_until": valid_until
    }, headers=headers)

    # 1. Calculation WITH target customer -> Contract Price 4000.00
    res_vip = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_id,
        "customer_id": cust_id,
        "quantity": "1.00"
    }, headers=headers)
    assert res_vip.status_code == 200
    assert res_vip.json()["pricing_source"] == "CONTRACT"
    assert Decimal(res_vip.json()["final_unit_price"]) == Decimal("4000.00")

    # 2. Calculation WITHOUT customer -> Base Price 5000.00
    res_gen = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_id,
        "quantity": "1.00"
    }, headers=headers)
    assert res_gen.json()["pricing_source"] == "BASE_PRODUCT_PRICE"
    assert Decimal(res_gen.json()["final_unit_price"]) == Decimal("5000.00")


@pytest.mark.asyncio
async def test_expired_contract_price_not_applied(async_client: AsyncClient):
    """Verify expired contract rule is ignored and base price is used."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Expired Contract Org",
        "organization_slug": f"exp-contract-{uuid.uuid4().hex[:8]}",
        "email": "admin@expcontract.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Past Client"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Legacy Module", "sku": "LEG-01", "unit_price": "2000.00"}, headers=headers)).json()["id"]

    # Expired Contract Rule (ended yesterday)
    now = datetime.now(timezone.utc)
    valid_from = (now - timedelta(days=30)).isoformat()
    valid_until = (now - timedelta(days=1)).isoformat()

    await async_client.post("/api/v1/pricing/rules", json={
        "name": "Expired 2025 Deal",
        "rule_type": "contract",
        "product_id": prod_id,
        "customer_id": cust_id,
        "min_quantity": "1.00",
        "price_type": "override_price",
        "value": "1200.00",
        "priority": 1,
        "valid_from": valid_from,
        "valid_until": valid_until
    }, headers=headers)

    res = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_id,
        "customer_id": cust_id,
        "quantity": "1.00"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["pricing_source"] == "BASE_PRODUCT_PRICE"
    assert Decimal(res.json()["final_unit_price"]) == Decimal("2000.00")


@pytest.mark.asyncio
async def test_pricing_precedence(async_client: AsyncClient):
    """Verify Contract Price (Priority 1) overrides Volume Tier (Priority 20)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Precedence Org",
        "organization_slug": f"prec-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@precorg.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Special Partner"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Cloud Storage Node", "sku": "NODE-01", "unit_price": "1000.00"}, headers=headers)).json()["id"]

    # Volume Tier (50+ qty -> 800.00, priority 20)
    await async_client.post("/api/v1/pricing/rules", json={
        "name": "Volume 50+ Tier",
        "rule_type": "volume",
        "product_id": prod_id,
        "min_quantity": "50.00",
        "price_type": "override_price",
        "value": "800.00",
        "priority": 20
    }, headers=headers)

    # Contract Price for Special Partner (750.00, priority 1)
    await async_client.post("/api/v1/pricing/rules", json={
        "name": "Special Partner Fixed Rate",
        "rule_type": "contract",
        "product_id": prod_id,
        "customer_id": cust_id,
        "min_quantity": "1.00",
        "price_type": "override_price",
        "value": "750.00",
        "priority": 1
    }, headers=headers)

    res = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_id,
        "customer_id": cust_id,
        "quantity": "100.00"
    }, headers=headers)

    assert res.status_code == 200
    assert res.json()["pricing_source"] == "CONTRACT"
    assert Decimal(res.json()["final_unit_price"]) == Decimal("750.00")


@pytest.mark.asyncio
async def test_cross_tenant_pricing_isolation(async_client: AsyncClient):
    """Verify Organization B cannot access or use Organization A pricing rules."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org A Tenant",
        "organization_slug": f"org-a-{uuid.uuid4().hex[:8]}",
        "email": "adminA@tenant.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org B Tenant",
        "organization_slug": f"org-b-{uuid.uuid4().hex[:8]}",
        "email": "adminB@tenant.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    prod_a = (await async_client.post("/api/v1/products", json={"name": "Org A Secret Product", "sku": "SECRET-A", "unit_price": "500.00"}, headers=headers_a)).json()["id"]

    rule_a = (await async_client.post("/api/v1/pricing/rules", json={
        "name": "Org A Secret Discount",
        "rule_type": "volume",
        "product_id": prod_a,
        "min_quantity": "5.00",
        "price_type": "override_price",
        "value": "250.00",
        "priority": 10
    }, headers=headers_a)).json()

    # User B tries GET /pricing/rules/{rule_id} -> 404
    res_get = await async_client.get(f"/api/v1/pricing/rules/{rule_a['id']}", headers=headers_b)
    assert res_get.status_code == 404

    # User B tries calculate pricing on Org A product -> 404
    res_calc = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_a,
        "quantity": "10.00"
    }, headers=headers_b)
    assert res_calc.status_code == 404


@pytest.mark.asyncio
async def test_manual_unit_price_override(async_client: AsyncClient):
    """Verify manual unit_price override takes precedence and flags MANUAL_OVERRIDE source."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Manual Override Org",
        "organization_slug": f"man-override-{uuid.uuid4().hex[:8]}",
        "email": "admin@manoverride.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod_id = (await async_client.post("/api/v1/products", json={"name": "Custom Hardware", "sku": "HW-01", "unit_price": "3000.00"}, headers=headers)).json()["id"]

    res = await async_client.post("/api/v1/pricing/calculate", json={
        "product_id": prod_id,
        "quantity": "2.00",
        "manual_unit_price": "2750.00"
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["pricing_source"] == "MANUAL_OVERRIDE"
    assert Decimal(data["final_unit_price"]) == Decimal("2750.00")
    assert "Manual unit price override applied" in data["explanation"]


@pytest.mark.asyncio
async def test_quotation_uses_calculated_pricing_and_snapshots(async_client: AsyncClient):
    """Verify Quotation creation automatically uses Pricing Engine rules and snapshots historical unit price."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Quotation Pricing Integration Org",
        "organization_slug": f"q-pricing-{uuid.uuid4().hex[:8]}",
        "email": "admin@qpricing.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Acme Corp"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "SaaS Seat", "sku": "SAAS-01", "unit_price": "100.00"}, headers=headers)).json()["id"]

    # Create volume pricing rule: 50+ seats -> 75.00/unit
    await async_client.post("/api/v1/pricing/rules", json={
        "name": "50+ Seat Tier",
        "rule_type": "volume",
        "product_id": prod_id,
        "min_quantity": "50.00",
        "price_type": "override_price",
        "value": "75.00",
        "priority": 10
    }, headers=headers)

    # Create quotation without passing explicit item unit_price
    quot_res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "title": "50 Seat SaaS Subscription",
        "items": [
            {
                "product_id": prod_id,
                "quantity": "50.00"
            }
        ]
    }, headers=headers)

    assert quot_res.status_code == 201
    q_data = quot_res.json()
    assert Decimal(q_data["items"][0]["unit_price"]) == Decimal("75.00")
    assert Decimal(q_data["subtotal"]) == Decimal("3750.00")  # 50 * 75.00

    # Modify Product base price to 150.00
    await async_client.put(f"/api/v1/products/{prod_id}", json={"unit_price": "150.00"}, headers=headers)

    # Re-fetch quotation -> item unit price remains snapshotted at 75.00!
    fetched_q = (await async_client.get(f"/api/v1/quotations/{q_data['id']}", headers=headers)).json()
    assert Decimal(fetched_q["items"][0]["unit_price"]) == Decimal("75.00")
    assert Decimal(fetched_q["subtotal"]) == Decimal("3750.00")


@pytest.mark.asyncio
async def test_invalid_pricing_rule_data_rejected(async_client: AsyncClient):
    """Verify invalid pricing rule payload validation."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Validation Org",
        "organization_slug": f"val-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@valorg.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    prod_id = (await async_client.post("/api/v1/products", json={"name": "Test Item", "sku": "TI-01", "unit_price": "10.00"}, headers=headers)).json()["id"]

    # Negative value -> 422
    res1 = await async_client.post("/api/v1/pricing/rules", json={
        "name": "Invalid Price",
        "rule_type": "volume",
        "product_id": prod_id,
        "value": "-50.00"
    }, headers=headers)
    assert res1.status_code == 422

    # Contract rule missing customer_id -> 422
    res2 = await async_client.post("/api/v1/pricing/rules", json={
        "name": "Contract Without Customer",
        "rule_type": "contract",
        "product_id": prod_id,
        "value": "5.00"
    }, headers=headers)
    assert res2.status_code == 422
