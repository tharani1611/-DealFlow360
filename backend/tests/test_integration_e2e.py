import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from app.core.config import settings
from app.ai.service import ai_service
from app.ai.providers.mock import MockAIProvider


@pytest.fixture(autouse=True)
def use_mock_ai_provider(monkeypatch):
    """Ensure AI uses MockAIProvider for deterministic offline execution during tests."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    monkeypatch.setattr(ai_service, "_provider_override", MockAIProvider())


@pytest.mark.asyncio
async def test_e2e_full_crm_journey(async_client: AsyncClient):
    """
    FULL END-TO-END INTEGRATION TEST:
    Executes complete commercial CRM lifecycle:
    Registration -> Login -> Me -> Customer -> Contact -> Product -> Quotation -> Deal -> Activity -> AI Analysis -> Assistant.
    """
    hex_id = uuid.uuid4().hex[:8]
    org_slug = f"alpha-sales-{hex_id}"
    admin_email = f"admin@{org_slug}.com"
    password = "Password123!"

    # 1. Registration
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Alpha Sales Corp",
        "organization_slug": org_slug,
        "email": admin_email,
        "password": password,
        "full_name": "Alpha Admin"
    })
    assert reg_res.status_code == 201
    token_a = reg_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Get Me
    me_res = await async_client.get("/api/v1/auth/me", headers=headers_a)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == admin_email
    assert me_data["is_admin"] is True

    # 3. Create Customer
    cust_res = await async_client.post("/api/v1/customers", json={
        "name": "Apex Global Systems",
        "email": "contact@apexglobal.com",
        "phone": "+1-555-019-2834",
        "city": "San Francisco"
    }, headers=headers_a)
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    # 4. Create Contact
    contact_res = await async_client.post("/api/v1/contacts", json={
        "customer_id": cust_id,
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@apexglobal.com",
        "job_title": "VP of Technology",
        "is_primary": True
    }, headers=headers_a)
    assert contact_res.status_code == 201
    contact_id = contact_res.json()["id"]

    # 5. Create Product SKU
    prod_res = await async_client.post("/api/v1/products", json={
        "name": "Enterprise Cloud License",
        "sku": f"SKU-{hex_id.upper()}",
        "unit_price": "25000.00",
        "currency": "USD"
    }, headers=headers_a)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 6. Create Commercial Quotation
    quote_res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "notes": "Enterprise discount applied",
        "items": [
            {
                "product_id": prod_id,
                "description": "Enterprise License Pack",
                "quantity": 2,
                "unit_price": "25000.00"
            }
        ]
    }, headers=headers_a)
    assert quote_res.status_code == 201
    quote_data = quote_res.json()
    quote_id = quote_data["id"]
    assert Decimal(quote_data["total_amount"]) == Decimal("50000.00")

    # Transition Quotation: draft -> sent -> accepted
    sent_res = await async_client.put(f"/api/v1/quotations/{quote_id}", json={"status": "sent"}, headers=headers_a)
    assert sent_res.status_code == 200
    assert sent_res.json()["status"] == "sent"

    acc_res = await async_client.put(f"/api/v1/quotations/{quote_id}", json={"status": "accepted"}, headers=headers_a)
    assert acc_res.status_code == 200
    assert acc_res.json()["status"] == "accepted"

    # 7. Create Sales Deal
    deal_res = await async_client.post("/api/v1/deals", json={
        "title": "Apex Cloud Migration Opportunity",
        "customer_id": cust_id,
        "contact_id": contact_id,
        "quotation_id": quote_id,
        "value": "100000.00",
        "probability": 40,
        "stage": "new"
    }, headers=headers_a)
    assert deal_res.status_code == 201
    deal_id = deal_res.json()["id"]

    # Transition Deal Stage: new -> qualified -> proposal
    trans_res1 = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "qualified"}, headers=headers_a)
    assert trans_res1.status_code == 200
    assert trans_res1.json()["stage"] == "qualified"

    trans_res2 = await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "proposal"}, headers=headers_a)
    assert trans_res2.status_code == 200
    assert trans_res2.json()["stage"] == "proposal"

    # 8. Create CRM Activity for Deal
    act_res = await async_client.post("/api/v1/activities", json={
        "deal_id": deal_id,
        "customer_id": cust_id,
        "contact_id": contact_id,
        "activity_type": "call",
        "title": "Discuss proposal terms",
        "priority": "high"
    }, headers=headers_a)
    assert act_res.status_code == 201
    act_id = act_res.json()["id"]

    # Complete Activity
    comp_res = await async_client.post(f"/api/v1/activities/{act_id}/complete", headers=headers_a)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"

    # 9. AI Intelligence Integration
    sum_res = await async_client.post(f"/api/v1/ai/customers/{cust_id}/summary", headers=headers_a)
    assert sum_res.status_code == 200
    assert sum_res.json()["customer_name"] == "Apex Global Systems"

    ana_res = await async_client.post(f"/api/v1/ai/deals/{deal_id}/analysis", headers=headers_a)
    assert ana_res.status_code == 200
    assert ana_res.json()["deal_id"] == deal_id

    next_res = await async_client.post(f"/api/v1/ai/deals/{deal_id}/next-action", headers=headers_a)
    assert next_res.status_code == 200
    assert "title" in next_res.json()

    asst_res = await async_client.post("/api/v1/ai/assistant", json={"question": "Summarize Apex deal status"}, headers=headers_a)
    assert asst_res.status_code == 200
    assert "answer" in asst_res.json()


@pytest.mark.asyncio
async def test_e2e_multi_tenant_isolation_security(async_client: AsyncClient):
    """
    CRITICAL SECURITY E2E TEST:
    Verify Organization A cannot read, update, delete, or run AI on Organization B resources.
    Returns 404 Not Found across all boundaries.
    """
    slug_a = f"tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"tenant-b-{uuid.uuid4().hex[:8]}"

    # Org A
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org A", "organization_slug": slug_a,
        "email": "adminA@orga.com", "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Org B
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org B", "organization_slug": slug_b,
        "email": "adminB@orgb.com", "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create Org B Resources
    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Secret Account B"}, headers=headers_b)).json()["id"]
    deal_b = (await async_client.post("/api/v1/deals", json={"customer_id": cust_b, "title": "Secret Deal B"}, headers=headers_b)).json()["id"]

    # User A attempts cross-tenant access to Org B -> 404
    assert (await async_client.get(f"/api/v1/customers/{cust_b}", headers=headers_a)).status_code == 404
    assert (await async_client.get(f"/api/v1/deals/{deal_b}", headers=headers_a)).status_code == 404
    assert (await async_client.delete(f"/api/v1/customers/{cust_b}", headers=headers_a)).status_code == 404
    assert (await async_client.post(f"/api/v1/ai/customers/{cust_b}/summary", headers=headers_a)).status_code == 404
    assert (await async_client.post(f"/api/v1/ai/deals/{deal_b}/analysis", headers=headers_a)).status_code == 404
