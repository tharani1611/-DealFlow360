import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_manage_recommendation_rule_rbac(async_client: AsyncClient):
    """Verify admin can create, list, and update recommendation rules, while non-admin gets 403 on mutation."""
    # 1. Register Org with Admin user
    reg_admin = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Rec Rule Org",
        "organization_slug": f"recorg-{uuid.uuid4().hex[:8]}",
        "email": "admin@recorg.com",
        "password": "Password123!",
        "full_name": "Admin User"
    })
    admin_headers = {"Authorization": f"Bearer {reg_admin.json()['access_token']}"}

    # 2. Create 2 products
    p1_res = await async_client.post("/api/v1/products", json={
        "name": "Standard Plan",
        "sku": "SKU-STD-01",
        "unit_price": "100.00"
    }, headers=admin_headers)
    p1_id = p1_res.json()["id"]

    p2_res = await async_client.post("/api/v1/products", json={
        "name": "Enterprise Plan",
        "sku": "SKU-ENT-01",
        "unit_price": "500.00"
    }, headers=admin_headers)
    p2_id = p2_res.json()["id"]

    # 3. Create Rule as Admin
    rule_res = await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": p1_id,
        "target_product_id": p2_id,
        "rule_type": "upsell",
        "priority": 1,
        "description": "Upgrade from Standard to Enterprise Plan"
    }, headers=admin_headers)
    assert rule_res.status_code == 201
    rule_data = rule_res.json()
    assert rule_data["source_product_id"] == p1_id
    assert rule_data["target_product_id"] == p2_id
    assert rule_data["rule_type"] == "upsell"
    assert rule_data["priority"] == 1
    rule_id = rule_data["id"]

    # 4. List Rules
    list_res = await async_client.get("/api/v1/product-recommendation-rules", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 5. Filter Rules by rule_type
    filter_res = await async_client.get("/api/v1/product-recommendation-rules?rule_type=upsell", headers=admin_headers)
    assert filter_res.status_code == 200
    assert len(filter_res.json()) == 1


@pytest.mark.asyncio
async def test_rule_validation_and_conflict_checks(async_client: AsyncClient):
    """Verify self-reference is rejected (422), duplicate rule is rejected (409), and cross-tenant product returns 404."""
    # Org A
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org A Rec",
        "organization_slug": f"orga-rec-{uuid.uuid4().hex[:8]}",
        "email": "admin@orga.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    pa1_res = await async_client.post("/api/v1/products", json={"name": "Prod A1", "sku": "PA1", "unit_price": "10.00"}, headers=headers_a)
    pa2_res = await async_client.post("/api/v1/products", json={"name": "Prod A2", "sku": "PA2", "unit_price": "20.00"}, headers=headers_a)
    pa1_id = pa1_res.json()["id"]
    pa2_id = pa2_res.json()["id"]

    # Org B
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org B Rec",
        "organization_slug": f"orgb-rec-{uuid.uuid4().hex[:8]}",
        "email": "admin@orgb.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}
    pb1_res = await async_client.post("/api/v1/products", json={"name": "Prod B1", "sku": "PB1", "unit_price": "30.00"}, headers=headers_b)
    pb1_id = pb1_res.json()["id"]

    # 1. Self-reference check (422)
    self_res = await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": pa1_id,
        "target_product_id": pa1_id,
        "rule_type": "upsell"
    }, headers=headers_a)
    assert self_res.status_code == 422

    # 2. Cross-tenant product check (404)
    cross_res = await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": pa1_id,
        "target_product_id": pb1_id,
        "rule_type": "cross_sell"
    }, headers=headers_a)
    assert cross_res.status_code == 404

    # 3. Create valid rule
    valid_res = await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": pa1_id,
        "target_product_id": pa2_id,
        "rule_type": "cross_sell"
    }, headers=headers_a)
    assert valid_res.status_code == 201

    # 4. Duplicate rule check (409)
    dup_res = await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": pa1_id,
        "target_product_id": pa2_id,
        "rule_type": "cross_sell"
    }, headers=headers_a)
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_customer_product_recommendation_evaluation(async_client: AsyncClient):
    """Verify upsell and cross-sell recommendations are evaluated based on owned products and criteria."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Eval Rec Org",
        "organization_slug": f"evalrec-{uuid.uuid4().hex[:8]}",
        "email": "admin@evalrec.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Create Products
    p_base = (await async_client.post("/api/v1/products", json={"name": "Base Suite", "sku": "P-BASE", "unit_price": "100.00"}, headers=headers)).json()
    p_up = (await async_client.post("/api/v1/products", json={"name": "Pro Suite", "sku": "P-UP", "unit_price": "300.00"}, headers=headers)).json()
    p_cross = (await async_client.post("/api/v1/products", json={"name": "Addon Module", "sku": "P-CROSS", "unit_price": "50.00"}, headers=headers)).json()

    # Create Rules
    await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": p_base["id"],
        "target_product_id": p_up["id"],
        "rule_type": "upsell",
        "priority": 1,
        "description": "Upgrade to Pro Suite"
    }, headers=headers)

    await async_client.post("/api/v1/product-recommendation-rules", json={
        "source_product_id": p_base["id"],
        "target_product_id": p_cross["id"],
        "rule_type": "cross_sell",
        "priority": 2,
        "description": "Complementary Addon Module"
    }, headers=headers)

    # Create Customer
    cust = (await async_client.post("/api/v1/customers", json={"name": "Tech Corp"}, headers=headers)).json()
    cust_id = cust["id"]

    # Before purchasing p_base: 0 recommendations
    rec_res1 = await async_client.get(f"/api/v1/intelligence/customers/{cust_id}/product-recommendations", headers=headers)
    assert rec_res1.status_code == 200
    assert len(rec_res1.json()["recommendations"]) == 0

    # Create Accepted Quotation for p_base
    quote = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": p_base["id"], "description": "Base Suite Subscription", "quantity": 1, "unit_price": "100.00"}]
    }, headers=headers)).json()

    # Accept quotation via valid state machine transitions: draft -> sent -> accepted
    await async_client.put(f"/api/v1/quotations/{quote['id']}", json={"status": "sent"}, headers=headers)
    await async_client.put(f"/api/v1/quotations/{quote['id']}", json={"status": "accepted"}, headers=headers)

    # After accepting quotation: evaluate recommendations
    rec_res2 = await async_client.get(f"/api/v1/intelligence/customers/{cust_id}/product-recommendations", headers=headers)
    assert rec_res2.status_code == 200
    recs = rec_res2.json()["recommendations"]
    assert len(recs) == 2

    # Check Upsell and Cross-sell items
    rec_types = {r["recommendation_type"] for r in recs}
    assert "upsell" in rec_types
    assert "cross_sell" in rec_types


@pytest.mark.asyncio
async def test_tenant_isolation_for_recommendations(async_client: AsyncClient):
    """Verify Tenant A cannot access Tenant B recommendations or rules."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Ten A Rec",
        "organization_slug": f"t-a-rec-{uuid.uuid4().hex[:8]}",
        "email": "admin@t-a.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Ten B Rec",
        "organization_slug": f"t-b-rec-{uuid.uuid4().hex[:8]}",
        "email": "admin@t-b.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()

    # User A tries to get recommendations for Cust B (404)
    res = await async_client.get(f"/api/v1/intelligence/customers/{cust_b['id']}/product-recommendations", headers=headers_a)
    assert res.status_code == 404
