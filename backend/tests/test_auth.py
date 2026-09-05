import pytest
import uuid
from datetime import timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    """Verify registration creates Organization + Admin User atomically and returns JWT."""
    unique_slug = f"acme-reg-{uuid.uuid4().hex[:8]}"
    payload = {
        "organization_name": "Acme Test Corp",
        "organization_slug": unique_slug,
        "email": "Admin@AcmeTest.com",  # Test normalization to lowercase
        "full_name": "Acme Administrator",
        "password": "SuperSecretPassword123!"
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Check user response structure (no password_hash)
    assert "user" in data
    assert "password_hash" not in data["user"]
    assert data["user"]["email"] == "admin@acmetest.com"
    assert data["user"]["is_admin"] is True
    assert data["user"]["is_active"] is True

    # Check organization response structure
    assert "organization" in data
    assert data["organization"]["slug"] == unique_slug
    assert data["organization"]["name"] == "Acme Test Corp"

    # Check access token
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_slug_rejected(async_client: AsyncClient):
    """Verify duplicate organization slug registration returns 409 Conflict."""
    unique_slug = f"dup-slug-{uuid.uuid4().hex[:8]}"
    payload = {
        "organization_name": "First Corp",
        "organization_slug": unique_slug,
        "email": "owner@firstcorp.com",
        "password": "Password123!"
    }

    resp1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    payload2 = {
        "organization_name": "Second Corp",
        "organization_slug": unique_slug,
        "email": "owner@secondcorp.com",
        "password": "Password123!"
    }
    resp2 = await async_client.post("/api/v1/auth/register", json=payload2)
    assert resp2.status_code == 409
    assert "already taken" in resp2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_register_invalid_slug_format(async_client: AsyncClient):
    """Verify invalid slug format (uppercase, spaces, special chars) is rejected with 422."""
    invalid_slugs = ["Acme Corp", "acme_corp", "acme/corp", "acme@corp", ""]
    for slug in invalid_slugs:
        payload = {
            "organization_name": "Test Corp",
            "organization_slug": slug,
            "email": "user@test.com",
            "password": "Password123!"
        }
        resp = await async_client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_password(async_client: AsyncClient):
    """Verify short or empty passwords are rejected with 422."""
    short_pwd_payload = {
        "organization_name": "Short Pwd Corp",
        "organization_slug": f"short-pwd-{uuid.uuid4().hex[:6]}",
        "email": "user@short.com",
        "password": "123"
    }
    resp = await async_client.post("/api/v1/auth/register", json=short_pwd_payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Verify successful login returns user details and JWT access token."""
    slug = f"login-org-{uuid.uuid4().hex[:8]}"
    reg_payload = {
        "organization_name": "Login Test Org",
        "organization_slug": slug,
        "email": "loginuser@testorg.com",
        "password": "LoginPassword123!"
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201

    login_payload = {
        "organization_slug": slug,
        "email": "LoginUser@TestOrg.com",
        "password": "LoginPassword123!"
    }
    resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@testorg.com"
    assert data["organization"]["slug"] == slug
    assert "password_hash" not in data["user"]


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(async_client: AsyncClient):
    """Verify login with wrong password returns 401 Unauthorized with generic error message."""
    slug = f"wrong-pwd-{uuid.uuid4().hex[:8]}"
    reg_payload = {
        "organization_name": "Wrong Pwd Org",
        "organization_slug": slug,
        "email": "user@wrongpwd.com",
        "password": "CorrectPassword123!"
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "organization_slug": slug,
        "email": "user@wrongpwd.com",
        "password": "WRONGPassword123!"
    }
    resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid organization, email, or password"


@pytest.mark.asyncio
async def test_login_unknown_organization_rejected(async_client: AsyncClient):
    """Verify login with non-existent organization slug returns generic 401."""
    login_payload = {
        "organization_slug": "non-existent-org-slug-xyz",
        "email": "someone@test.com",
        "password": "Password123!"
    }
    resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid organization, email, or password"


@pytest.mark.asyncio
async def test_login_unknown_user_rejected(async_client: AsyncClient):
    """Verify login with non-existent email in valid organization returns generic 401."""
    slug = f"known-org-{uuid.uuid4().hex[:8]}"
    await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Known Org",
        "organization_slug": slug,
        "email": "realuser@known.com",
        "password": "Password123!"
    })

    resp = await async_client.post("/api/v1/auth/login", json={
        "organization_slug": slug,
        "email": "ghostuser@known.com",
        "password": "Password123!"
    })
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid organization, email, or password"


@pytest.mark.asyncio
async def test_login_inactive_user_rejected(async_client: AsyncClient):
    """Verify inactive user account cannot authenticate (returns 401)."""
    slug = f"inactive-u-org-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Inactive User Org",
        "organization_slug": slug,
        "email": "inactiveuser@test.com",
        "password": "Password123!"
    })
    user_id = reg_resp.json()["user"]["id"]

    # Deactivate user in database
    async with AsyncSessionLocal() as session:
        user = await session.get(User, uuid.UUID(user_id))
        user.is_active = False
        await session.commit()

    resp = await async_client.post("/api/v1/auth/login", json={
        "organization_slug": slug,
        "email": "inactiveuser@test.com",
        "password": "Password123!"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_organization_rejected(async_client: AsyncClient):
    """Verify inactive organization cannot authenticate (returns 401)."""
    slug = f"inactive-org-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Disabled Org",
        "organization_slug": slug,
        "email": "admin@disabledorg.com",
        "password": "Password123!"
    })
    org_id = reg_resp.json()["organization"]["id"]

    # Deactivate organization in database
    async with AsyncSessionLocal() as session:
        org = await session.get(Organization, uuid.UUID(org_id))
        org.is_active = False
        await session.commit()

    resp = await async_client.post("/api/v1/auth/login", json={
        "organization_slug": slug,
        "email": "admin@disabledorg.com",
        "password": "Password123!"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_multi_tenant_same_email_different_organizations(async_client: AsyncClient):
    """
    CRITICAL MULTI-TENANT TEST:
    Verify same email address in Org A and Org B authenticates strictly against their respective organization.
    """
    email = "shared_admin@multi-tenant-test.com"
    slug_a = f"org-tenant-a-{uuid.uuid4().hex[:6]}"
    slug_b = f"org-tenant-b-{uuid.uuid4().hex[:6]}"

    # Register Org A
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant Organization A",
        "organization_slug": slug_a,
        "email": email,
        "password": "PasswordOrgA123!"
    })
    assert reg_a.status_code == 201
    user_a_id = reg_a.json()["user"]["id"]

    # Register Org B with SAME email but different password & organization
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant Organization B",
        "organization_slug": slug_b,
        "email": email,
        "password": "PasswordOrgB123!"
    })
    assert reg_b.status_code == 201
    user_b_id = reg_b.json()["user"]["id"]

    assert user_a_id != user_b_id

    # Authenticate Org A
    login_a = await async_client.post("/api/v1/auth/login", json={
        "organization_slug": slug_a,
        "email": email,
        "password": "PasswordOrgA123!"
    })
    assert login_a.status_code == 200
    assert login_a.json()["user"]["id"] == user_a_id
    assert login_a.json()["organization"]["slug"] == slug_a

    # Authenticate Org B
    login_b = await async_client.post("/api/v1/auth/login", json={
        "organization_slug": slug_b,
        "email": email,
        "password": "PasswordOrgB123!"
    })
    assert login_b.status_code == 200
    assert login_b.json()["user"]["id"] == user_b_id
    assert login_b.json()["organization"]["slug"] == slug_b

    # Attempt cross-authentication: Password B against Org A -> Must fail 401
    cross_login = await async_client.post("/api/v1/auth/login", json={
        "organization_slug": slug_a,
        "email": email,
        "password": "PasswordOrgB123!"
    })
    assert cross_login.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns current user profile with valid Bearer token."""
    slug = f"me-org-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Me Endpoint Org",
        "organization_slug": slug,
        "email": "meuser@test.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == user_id
    assert data["email"] == "meuser@test.com"
    assert data["organization"]["slug"] == slug
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_get_me_missing_token_rejected(async_client: AsyncClient):
    """Verify /me without Authorization header returns 401 Unauthorized."""
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token_rejected(async_client: AsyncClient):
    """Verify /me with corrupted/tampered JWT token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer invalid.jwt.token.string"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_expired_token_rejected(async_client: AsyncClient):
    """Verify /me with expired JWT token returns 401 Unauthorized."""
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        expires_delta=timedelta(seconds=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_malformed_uuid_subject_rejected(async_client: AsyncClient):
    """Verify /me with non-UUID subject in JWT returns 401 Unauthorized."""
    bad_subject_token = create_access_token(subject="not-a-valid-uuid")
    headers = {"Authorization": f"Bearer {bad_subject_token}"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_deleted_user_rejected(async_client: AsyncClient):
    """Verify /me with valid token for deleted user returns 401 Unauthorized."""
    fake_user_id = str(uuid.uuid4())
    token = create_access_token(subject=fake_user_id)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_deactivated_user_rejected(async_client: AsyncClient):
    """Verify /me returns 401 if user account is deactivated after token issuance."""
    slug = f"deact-me-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Deact User Org",
        "organization_slug": slug,
        "email": "deactuser@test.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]

    # Deactivate user in DB
    async with AsyncSessionLocal() as session:
        user = await session.get(User, uuid.UUID(user_id))
        user.is_active = False
        await session.commit()

    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
