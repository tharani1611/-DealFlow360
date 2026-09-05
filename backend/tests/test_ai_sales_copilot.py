import pytest
import uuid
from httpx import AsyncClient
from app.core.config import settings
from app.ai.service import ai_service
from app.ai.providers.mock import MockAIProvider


@pytest.fixture(autouse=True)
def use_mock_ai_provider(monkeypatch):
    """Fixture ensuring AI uses MockAIProvider and AI_ENABLED=True for test cases."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    monkeypatch.setattr(ai_service, "_provider_override", MockAIProvider())


@pytest.mark.asyncio
async def test_copilot_chat_endpoint(async_client: AsyncClient):
    """Verify authenticated user can query AI Sales Copilot."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Copilot Org",
        "organization_slug": f"copilot-{uuid.uuid4().hex[:8]}",
        "email": "admin@copilot.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query Copilot for Pipeline intent
    res = await async_client.post(
        "/api/v1/copilot/chat",
        json={"message": "Summarize my open sales pipeline and revenue forecast."},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()

    assert "answer" in data
    assert data["intent"] == "PIPELINE"
    assert "evidence" in data
    assert len(data["evidence"]) >= 1
    assert data["metadata"]["provider"] == "mock"


@pytest.mark.asyncio
async def test_deal_qa_endpoint(async_client: AsyncClient):
    """Verify deal-specific Q&A endpoint."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Deal QA Org",
        "organization_slug": f"dealqa-{uuid.uuid4().hex[:8]}",
        "email": "admin@dealqa.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Deal QA Cust"}, headers=headers)).json()["id"]
    deal_id = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Big Enterprise Deal", "value": "120000.00"}, headers=headers)).json()["id"]

    res = await async_client.post(
        f"/api/v1/copilot/deals/{deal_id}/qa",
        json={"question": "Why is this deal requiring attention?"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()

    assert data["deal_id"] == deal_id
    assert "answer" in data
    assert len(data["key_facts"]) >= 1


@pytest.mark.asyncio
async def test_cross_tenant_copilot_isolation(async_client: AsyncClient):
    """Verify Copilot never accesses another organization's data."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org Alpha",
        "organization_slug": f"org-a-{uuid.uuid4().hex[:8]}",
        "email": "userA@orga.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Org Beta",
        "organization_slug": f"org-b-{uuid.uuid4().hex[:8]}",
        "email": "userB@orgb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Secret Beta Customer"}, headers=headers_b)).json()["id"]
    deal_b = (await async_client.post("/api/v1/deals", json={"customer_id": cust_b, "title": "Secret Beta Deal"}, headers=headers_b)).json()["id"]

    # User A tries to pass deal_b ID in copilot request context -> 404 on deal QA
    qa_res = await async_client.post(
        f"/api/v1/copilot/deals/{deal_b}/qa",
        json={"question": "What is secret about this deal?"},
        headers=headers_a
    )
    assert qa_res.status_code == 404
