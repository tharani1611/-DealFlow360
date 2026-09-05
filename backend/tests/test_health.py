import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/health endpoint returns 200 OK with expected status."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/readiness endpoint returns 200 OK with status telemetry."""
    response = await async_client.get("/api/v1/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data


@pytest.mark.asyncio
async def test_not_implemented_module_endpoint(async_client: AsyncClient):
    """Verify placeholder module route returns 501 Not Implemented."""
    response = await async_client.get("/api/v1/users")
    assert response.status_code == 501
    assert "foundation is prepared" in response.json()["detail"]
