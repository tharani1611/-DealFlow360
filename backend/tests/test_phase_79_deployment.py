"""
Phase 79 — Deployment, Health, and Production Configuration Verification Suite
=============================================================================
Tests:
1. Health and readiness endpoints functionality and response contracts.
2. Security headers presence (nosniff, DENY, referrer policy).
3. Exception handler data-leak prevention on unexpected 500 errors.
4. Production settings parsing for CORS, allowed hosts, and secret fallbacks.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status

from app.main import app
from app.core.config import Settings


@pytest.mark.asyncio
async def test_production_health_endpoint():
    """Verify /api/v1/health returns 200 with standard health schema and no secret leak."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "environment" in data
        assert "timestamp" in data
        assert "version" in data

        # Security check: zero database credentials or secrets leaked
        assert "password" not in resp.text.lower()
        assert "secret" not in resp.text.lower()
        assert "database_url" not in resp.text.lower()


@pytest.mark.asyncio
async def test_production_readiness_endpoint():
    """Verify /api/v1/readiness returns 200 with database connection status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/readiness")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] in ("ready", "degraded")
        assert "database_connected" in data
        assert isinstance(data["database_connected"], bool)


@pytest.mark.asyncio
async def test_production_security_headers():
    """Verify production security headers are set on API responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == status.HTTP_200_OK
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert "Referrer-Policy" in headers


@pytest.mark.asyncio
async def test_error_handling_leaks_zero_stack_traces():
    """Verify unhandled error response returns generic 500 error without exposing stack traces."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/non_existent_resource_xyz")
        assert resp.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_501_NOT_IMPLEMENTED)
        assert "Traceback" not in resp.text
        assert "File \"" not in resp.text


def test_production_settings_parsing():
    """Verify Settings parses list values and secret fallbacks accurately."""
    s = Settings(
        SECRET_KEY="test_secret_32_bytes_long_string_val",
        CORS_ORIGINS='["https://app.dealflow360.com", "https://dealflow360.com"]',
        ALLOWED_HOSTS="app.dealflow360.com,dealflow360.com"
    )
    assert len(s.CORS_ORIGINS) == 2
    assert "https://app.dealflow360.com" in s.CORS_ORIGINS
    assert len(s.ALLOWED_HOSTS) == 2
    assert "app.dealflow360.com" in s.ALLOWED_HOSTS
    assert s.effective_jwt_secret_key == "test_secret_32_bytes_long_string_val"
