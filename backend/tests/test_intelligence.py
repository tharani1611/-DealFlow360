import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_deal_health_scoring_deterministic_and_bounds(async_client: AsyncClient):
    """Verify deterministic deal health score calculation, bounds (0-100), and status mapping."""
    # 1. Register Org & User
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Health Test Org",
        "organization_slug": f"health-org-{uuid.uuid4().hex[:8]}",
        "email": "admin@healthtest.com",
        "password": "Password123!"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Customer
    cust_res = await async_client.post("/api/v1/customers", json={"name": "Health Test Corp"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # 3. Create Deal in 'new' stage
    deal_res = await async_client.post("/api/v1/deals", json={
        "title": "Health Score Test Deal",
        "customer_id": cust_id,
        "value": "50000.00",
        "probability": 50,
        "stage": "new"
    }, headers=headers)
    deal_id = deal_res.json()["id"]

    # 4. Fetch Deal Health via API
    resp = await async_client.get(f"/api/v1/intelligence/deals/{deal_id}/health", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["deal_id"] == deal_id
    assert 0 <= data["health_score"] <= 100
    assert data["health_status"] in ("healthy", "stable", "at_risk", "critical")
    assert data["risk_level"] in ("low", "medium", "high", "critical")
    assert isinstance(data["risk_factors"], list)
    assert "metrics" in data


@pytest.mark.asyncio
async def test_won_and_lost_deal_health_extremes(async_client: AsyncClient):
    """Verify won deal scores exactly 100 and lost deal scores exactly 0."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Extremes Org",
        "organization_slug": f"extreme-{uuid.uuid4().hex[:8]}",
        "email": "admin@extreme.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    cust_res = await async_client.post("/api/v1/customers", json={"name": "Extreme Corp"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # Won Deal
    won_deal = await async_client.post("/api/v1/deals", json={
        "title": "Won Opportunity",
        "customer_id": cust_id,
        "value": "10000.00",
        "stage": "won"
    }, headers=headers)
    won_id = won_deal.json()["id"]

    won_health = await async_client.get(f"/api/v1/intelligence/deals/{won_id}/health", headers=headers)
    assert won_health.status_code == 200
    assert won_health.json()["health_score"] == 100
    assert won_health.json()["health_status"] == "healthy"

    # Lost Deal
    lost_deal = await async_client.post("/api/v1/deals", json={
        "title": "Lost Opportunity",
        "customer_id": cust_id,
        "value": "10000.00",
        "stage": "lost",
        "lost_reason": "Price too high"
    }, headers=headers)
    lost_id = lost_deal.json()["id"]

    lost_health = await async_client.get(f"/api/v1/intelligence/deals/{lost_id}/health", headers=headers)
    assert lost_health.status_code == 200
    assert lost_health.json()["health_score"] == 0
    assert lost_health.json()["health_status"] == "critical"


@pytest.mark.asyncio
async def test_customer_engagement_telemetry(async_client: AsyncClient):
    """Verify customer engagement score, status, and cooling detection telemetry."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Engagement Org",
        "organization_slug": f"eng-{uuid.uuid4().hex[:8]}",
        "email": "admin@eng.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    cust_res = await async_client.post("/api/v1/customers", json={"name": "Engaged Customer Corp"}, headers=headers)
    cust_id = cust_res.json()["id"]

    resp = await async_client.get(f"/api/v1/intelligence/customers/{cust_id}/engagement", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["customer_id"] == cust_id
    assert 0 <= data["engagement_score"] <= 100
    assert data["engagement_status"] in ("highly_engaged", "engaged", "cooling", "cold")
    assert isinstance(data["is_going_cold"], bool)
    assert "metrics" in data


@pytest.mark.asyncio
async def test_sales_briefing_generation(async_client: AsyncClient):
    """Verify executive sales briefing endpoint returns structured briefing facts and talking points."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Briefing Org",
        "organization_slug": f"briefing-{uuid.uuid4().hex[:8]}",
        "email": "admin@briefing.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    cust_res = await async_client.post("/api/v1/customers", json={"name": "Acme Global"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # Contact
    await async_client.post("/api/v1/contacts", json={
        "customer_id": cust_id,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@acme.com",
        "is_primary": True
    }, headers=headers)

    brief_res = await async_client.get(f"/api/v1/intelligence/customers/{cust_id}/briefing", headers=headers)
    assert brief_res.status_code == 200
    bdata = brief_res.json()

    assert bdata["customer_id"] == cust_id
    assert bdata["customer_name"] == "Acme Global"
    assert bdata["primary_contact_name"] == "Jane Doe"
    assert isinstance(bdata["talking_points"], list)
    assert len(bdata["talking_points"]) > 0
    assert "suggested_followup_message" in bdata


@pytest.mark.asyncio
async def test_dashboard_pipeline_intelligence(async_client: AsyncClient):
    """Verify executive dashboard CRM pipeline metrics aggregation."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Pipeline Org",
        "organization_slug": f"pipe-{uuid.uuid4().hex[:8]}",
        "email": "admin@pipe.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    dash_res = await async_client.get("/api/v1/intelligence/dashboard", headers=headers)
    assert dash_res.status_code == 200
    ddata = dash_res.json()

    assert "pipeline" in ddata
    assert "open_pipeline_value" in ddata["pipeline"]
    assert "weighted_pipeline_value" in ddata["pipeline"]
    assert "deal_health_counts" in ddata
    assert "deals_at_risk" in ddata
    assert "customers_going_cold" in ddata


@pytest.mark.asyncio
async def test_intelligence_multi_tenant_security_isolation(async_client: AsyncClient):
    """Verify tenant A cannot request intelligence telemetry for tenant B resources (HTTP 404)."""
    # Tenant A
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant A Org",
        "organization_slug": f"ten-a-{uuid.uuid4().hex[:8]}",
        "email": "admin@tenantA.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    # Tenant B
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant B Org",
        "organization_slug": f"ten-b-{uuid.uuid4().hex[:8]}",
        "email": "admin@tenantB.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Create resource in Tenant A
    cust_a = await async_client.post("/api/v1/customers", json={"name": "Customer A"}, headers=headers_a)
    cust_a_id = cust_a.json()["id"]

    deal_a = await async_client.post("/api/v1/deals", json={
        "title": "Deal A",
        "customer_id": cust_a_id,
        "value": "20000.00"
    }, headers=headers_a)
    deal_a_id = deal_a.json()["id"]

    # Tenant B attempts to access Tenant A intelligence
    dh_res = await async_client.get(f"/api/v1/intelligence/deals/{deal_a_id}/health", headers=headers_b)
    assert dh_res.status_code == 404

    ce_res = await async_client.get(f"/api/v1/intelligence/customers/{cust_a_id}/engagement", headers=headers_b)
    assert ce_res.status_code == 404

    sb_res = await async_client.get(f"/api/v1/intelligence/customers/{cust_a_id}/briefing", headers=headers_b)
    assert sb_res.status_code == 404
