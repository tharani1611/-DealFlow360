import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_customer_360_and_product_360_intelligence_e2e(async_client: AsyncClient):
    """End-to-end integration test verifying Customer 360 & Product 360 Intelligence REST endpoints."""
    # 1. Register test organization and admin user
    slug = f"intelorg-{uuid.uuid4().hex[:8]}"
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Intel Corp",
        "organization_slug": slug,
        "email": f"admin@{slug}.com",
        "password": "Password123!",
        "full_name": "Intelligence Admin"
    })
    assert reg.status_code == 201
    auth_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # 2. Create customer
    cust_res = await async_client.post("/api/v1/customers", json={
        "name": "Acme Global Solutions",
        "email": "info@acme.com",
        "industry": "Cloud Infrastructure"
    }, headers=auth_headers)
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    # 3. Create products
    p1_res = await async_client.post("/api/v1/products", json={
        "name": "Cloud Host Pro",
        "sku": f"CHP-{uuid.uuid4().hex[:4]}",
        "unit_price": 5000.00
    }, headers=auth_headers)
    assert p1_res.status_code == 201
    p1_id = p1_res.json()["id"]

    p2_res = await async_client.post("/api/v1/products", json={
        "name": "Security Shield Addon",
        "sku": f"SSA-{uuid.uuid4().hex[:4]}",
        "unit_price": 2000.00
    }, headers=auth_headers)
    assert p2_res.status_code == 201
    p2_id = p2_res.json()["id"]

    # 4. Create deal for customer
    deal_res = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "title": "Cloud Infrastructure Upgrade",
        "value": 15000.00,
        "stage": "proposal",
        "probability": 75
    }, headers=auth_headers)
    assert deal_res.status_code == 201

    # 5. Create quotation with both products
    quote_res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "valid_until": "2028-12-31",
        "items": [
            {"product_id": p1_id, "quantity": 2, "unit_price": 5000.00},
            {"product_id": p2_id, "quantity": 1, "unit_price": 2000.00}
        ]
    }, headers=auth_headers)
    assert quote_res.status_code == 201
    quote_id = quote_res.json()["id"]

    # 6. Test GET /api/v1/intelligence/customers/{customer_id}/360
    c360_res = await async_client.get(
        f"/api/v1/intelligence/customers/{cust_id}/360",
        headers=auth_headers
    )
    assert c360_res.status_code == 200
    c360_data = c360_res.json()

    assert c360_data["customer_id"] == cust_id
    assert c360_data["customer_name"] == "Acme Global Solutions"
    assert "financials" in c360_data
    assert "health" in c360_data
    assert "trends" in c360_data
    assert c360_data["health"]["health_score"] >= 0
    assert len(c360_data["health"]["positive_drivers"]) >= 1

    # 7. Test GET /api/v1/intelligence/products/{product_id}/360
    p360_res = await async_client.get(
        f"/api/v1/intelligence/products/{p1_id}/360",
        headers=auth_headers
    )
    assert p360_res.status_code == 200
    p360_data = p360_res.json()

    assert p360_data["product_id"] == p1_id
    assert p360_data["name"] == "Cloud Host Pro"
    assert "performance" in p360_data
    assert p360_data["performance"]["units_quoted"] == 2
    assert "affinities" in p360_data


@pytest.mark.asyncio
async def test_tenant_isolation_on_customer_and_product_intelligence(async_client: AsyncClient):
    """Verifies Tenant B cannot access Tenant A's customer or product intelligence."""
    # Org A
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org Alpha",
        "organization_slug": f"orga-{uuid.uuid4().hex[:8]}",
        "email": f"user@{uuid.uuid4().hex[:8]}.com",
        "password": "Password123!",
        "full_name": "User Alpha"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    # Org B
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org Beta",
        "organization_slug": f"orgb-{uuid.uuid4().hex[:8]}",
        "email": f"user@{uuid.uuid4().hex[:8]}.com",
        "password": "Password123!",
        "full_name": "User Beta"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Org A Customer & Product
    cust_a = await async_client.post("/api/v1/customers", json={"name": "Alpha Cust"}, headers=headers_a)
    prod_a = await async_client.post("/api/v1/products", json={"name": "Alpha Prod", "sku": f"SKU-{uuid.uuid4().hex[:4]}", "unit_price": 100}, headers=headers_a)

    cust_a_id = cust_a.json()["id"]
    prod_a_id = prod_a.json()["id"]

    # Org B attempts to access Org A intelligence -> 404 Not Found
    res_c = await async_client.get(f"/api/v1/intelligence/customers/{cust_a_id}/360", headers=headers_b)
    assert res_c.status_code == 404

    res_p = await async_client.get(f"/api/v1/intelligence/products/{prod_a_id}/360", headers=headers_b)
    assert res_p.status_code == 404
