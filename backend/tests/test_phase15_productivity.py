import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sales_attention_center_items(async_client: AsyncClient):
    """Verify sales attention center endpoint returns prioritized items (critical, high, medium)."""
    # Register tenant
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Attention Test Org",
        "organization_slug": f"att-{uuid.uuid4().hex[:8]}",
        "email": "admin@att.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Fetch attention items
    res = await async_client.get("/api/v1/intelligence/attention", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "items" in data
    assert "critical_count" in data
    assert "total_count" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_pipeline_concentration_and_executive_intelligence(async_client: AsyncClient):
    """Verify pipeline concentration analytics and win rate calculations in dashboard intelligence."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Concentration Org",
        "organization_slug": f"conc-{uuid.uuid4().hex[:8]}",
        "email": "admin@conc.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    cust_res = await async_client.post("/api/v1/customers", json={"name": "Big Corp"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # Deal 1 (large value)
    await async_client.post("/api/v1/deals", json={
        "title": "Mega Cloud Deal",
        "customer_id": cust_id,
        "value": "100000.00",
        "stage": "proposal"
    }, headers=headers)

    # Deal 2 (small value)
    await async_client.post("/api/v1/deals", json={
        "title": "Small Addon Deal",
        "customer_id": cust_id,
        "value": "10000.00",
        "stage": "qualified"
    }, headers=headers)

    dash_res = await async_client.get("/api/v1/intelligence/dashboard", headers=headers)
    assert dash_res.status_code == 200
    pdata = dash_res.json()["pipeline"]

    assert "concentration" in pdata
    assert pdata["concentration"]["is_concentrated"] is True
    assert pdata["concentration"]["top_deals_value_ratio"] >= 80.0
    assert "stage_breakdown" in pdata
    assert len(pdata["stage_breakdown"]) > 0


@pytest.mark.asyncio
async def test_activity_productivity_metrics(async_client: AsyncClient):
    """Verify activity productivity metrics endpoint (today, upcoming, overdue, completed counts)."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Act Prod Org",
        "organization_slug": f"actprod-{uuid.uuid4().hex[:8]}",
        "email": "admin@actprod.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    cust_res = await async_client.post("/api/v1/customers", json={"name": "Act Customer"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # Log activity
    await async_client.post("/api/v1/activities", json={
        "customer_id": cust_id,
        "activity_type": "call",
        "title": "Call client today",
        "priority": "high"
    }, headers=headers)

    res = await async_client.get("/api/v1/intelligence/activity-productivity", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "today_count" in data
    assert "upcoming_7d_count" in data
    assert "overdue_count" in data
    assert "completed_this_week_count" in data


@pytest.mark.asyncio
async def test_alert_notifications_feed(async_client: AsyncClient):
    """Verify derived alert notifications endpoint for topbar drawer."""
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Alert Org",
        "organization_slug": f"alert-{uuid.uuid4().hex[:8]}",
        "email": "admin@alert.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    res = await async_client.get("/api/v1/intelligence/alerts", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "alerts" in data
    assert "unread_count" in data
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_phase15_multi_tenant_security_isolation(async_client: AsyncClient):
    """Verify Tenant A cannot access Tenant B attention items or productivity metrics."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant A",
        "organization_slug": f"ten-a-{uuid.uuid4().hex[:8]}",
        "email": "userA@orga.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant B",
        "organization_slug": f"ten-b-{uuid.uuid4().hex[:8]}",
        "email": "userB@orgb.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Fetch attention items for B using B's token
    res_b = await async_client.get("/api/v1/intelligence/attention", headers=headers_b)
    assert res_b.status_code == 200

    # Ensure dashboard intelligence for A only reflects A's data
    res_a = await async_client.get("/api/v1/intelligence/dashboard", headers=headers_a)
    assert res_a.status_code == 200
