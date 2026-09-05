import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_discount_policy_crud_and_tenant_isolation(async_client: AsyncClient):
    """Verify CRUD operations and multi-tenant isolation for discount policies."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Gov Org A",
        "organization_slug": f"gov-a-{uuid.uuid4().hex[:8]}",
        "email": "adminA@gova.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Gov Org B",
        "organization_slug": f"gov-b-{uuid.uuid4().hex[:8]}",
        "email": "adminB@govb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Create Policy in Org A (max discount 15%)
    pol_a_res = await async_client.post("/api/v1/discount-governance/policies", json={
        "name": "Standard 15% Max Discount",
        "scope": "organization",
        "max_discount_percent": "15.00",
        "priority": 100
    }, headers=headers_a)
    assert pol_a_res.status_code == 201
    pol_a_id = pol_a_res.json()["id"]

    # 2. List Policies in Org A -> 1 policy
    list_a = await async_client.get("/api/v1/discount-governance/policies", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    # 3. Org B cannot see Org A policy (404)
    assert (await async_client.get(f"/api/v1/discount-governance/policies/{pol_a_id}", headers=headers_b)).status_code == 404
    assert (await async_client.put(f"/api/v1/discount-governance/policies/{pol_a_id}", json={"name": "Hacked"}, headers=headers_b)).status_code == 404
    assert (await async_client.delete(f"/api/v1/discount-governance/policies/{pol_a_id}", headers=headers_b)).status_code == 404

    # 4. Update Policy in Org A
    upd_res = await async_client.put(f"/api/v1/discount-governance/policies/{pol_a_id}", json={
        "max_discount_percent": "20.00"
    }, headers=headers_a)
    assert upd_res.status_code == 200
    assert Decimal(upd_res.json()["max_discount_percent"]) == Decimal("20.00")


@pytest.mark.asyncio
async def test_discount_governance_evaluation_compliance_and_violations(async_client: AsyncClient):
    """Verify evaluation of discount compliance: within policy vs outside policy."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Gov Eval Org",
        "organization_slug": f"gov-eval-{uuid.uuid4().hex[:8]}",
        "email": "admin@goveval.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create policy max discount 10%
    await async_client.post("/api/v1/discount-governance/policies", json={
        "name": "10% Cap Policy",
        "scope": "organization",
        "max_discount_percent": "10.00"
    }, headers=headers)

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Gov Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Server", "sku": "SRV-GV", "unit_price": "1000.00"}, headers=headers)).json()["id"]

    # Quotation 1: 5% discount (within policy)
    q1 = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{
            "product_id": prod_id,
            "quantity": "1",
            "unit_price": "1000.00",
            "discount_percent": "5.00",
            "discount_amount": "50.00"
        }]
    }, headers=headers)).json()["id"]

    eval1 = await async_client.post(f"/api/v1/discount-governance/evaluate?quotation_id={q1}", headers=headers)
    assert eval1.status_code == 200
    res1 = eval1.json()
    assert res1["compliant"] is True
    assert res1["status"] == "WITHIN_POLICY"
    assert len(res1["violations"]) == 0

    # Quotation 2: 25% discount (outside policy violation)
    q2 = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{
            "product_id": prod_id,
            "quantity": "1",
            "unit_price": "1000.00",
            "discount_percent": "25.00",
            "discount_amount": "250.00"
        }]
    }, headers=headers)).json()["id"]

    eval2 = await async_client.post(f"/api/v1/discount-governance/evaluate?quotation_id={q2}", headers=headers)
    assert eval2.status_code == 200
    res2 = eval2.json()
    assert res2["compliant"] is False
    assert res2["status"] == "OUTSIDE_POLICY"
    assert len(res2["violations"]) >= 1
    assert res2["violations"][0]["violation_type"] == "MAX_DISCOUNT_PERCENT"
