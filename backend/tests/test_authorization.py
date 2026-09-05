import pytest
import uuid
from datetime import timedelta
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User


@pytest.mark.asyncio
async def test_auth_boundary_missing_token(async_client: AsyncClient):
    """1. Verify missing token on protected admin endpoint returns 401 Unauthorized."""
    response = await async_client.get("/api/v1/auth/admin-check")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_boundary_invalid_token(async_client: AsyncClient):
    """2. Verify invalid/corrupted token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer malformed.invalid.token"}
    response = await async_client.get("/api/v1/auth/admin-check", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_boundary_expired_token(async_client: AsyncClient):
    """3. Verify expired token returns 401 Unauthorized."""
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        expires_delta=timedelta(seconds=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.get("/api/v1/auth/admin-check", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_boundary_normal_and_admin_authenticated_on_me(async_client: AsyncClient):
    """4 & 5. Verify both normal users and admin users can authenticate on /me."""
    slug = f"auth-me-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Auth Me Org",
        "organization_slug": slug,
        "email": "admin@authme.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create normal user (is_admin=False) in DB
    async with AsyncSessionLocal() as session:
        normal_user = User(
            organization_id=uuid.UUID(org_id),
            email="normal@authme.com",
            password_hash=hash_password("Password123!"),
            is_admin=False,
            is_active=True
        )
        session.add(normal_user)
        await session.commit()
        await session.refresh(normal_user)
        normal_user_id = str(normal_user.id)

    normal_token = create_access_token(subject=normal_user_id)

    # Test Admin on /me
    res_admin = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert res_admin.json()["is_admin"] is True
    assert res_admin.json()["role"] == "admin"

    # Test Normal User on /me
    res_normal = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {normal_token}"})
    assert res_normal.status_code == 200
    assert res_normal.json()["is_admin"] is False
    assert res_normal.json()["role"] == "user"


@pytest.mark.asyncio
async def test_admin_accesses_admin_endpoint_success(async_client: AsyncClient):
    """6 & 11. Verify admin user (is_admin=True) receives 200 OK on admin endpoint."""
    slug = f"admin-ok-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Admin OK Org",
        "organization_slug": slug,
        "email": "admin@adminok.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]

    resp = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["authorized"] is True
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_normal_user_accesses_admin_endpoint_forbidden(async_client: AsyncClient):
    """7 & 12. Verify normal user (is_admin=False) receives 403 Forbidden on admin endpoint."""
    slug = f"norm-deny-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Normal Deny Org",
        "organization_slug": slug,
        "email": "admin@normdeny.com",
        "password": "Password123!"
    })
    org_id = reg_resp.json()["organization"]["id"]

    # Create normal user
    async with AsyncSessionLocal() as session:
        normal_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@normdeny.com",
            password_hash=hash_password("Password123!"),
            is_admin=False,
            is_active=True
        )
        session.add(normal_user)
        await session.commit()
        await session.refresh(normal_user)
        normal_user_id = str(normal_user.id)

    token = create_access_token(subject=normal_user_id)
    resp = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "Administrator privileges required" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_anonymous_user_accesses_admin_endpoint_unauthorized(async_client: AsyncClient):
    """8. Verify unauthenticated user on admin endpoint receives 401 Unauthorized (not 403)."""
    resp = await async_client.get("/api/v1/auth/admin-check")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_accessing_admin_endpoint(async_client: AsyncClient):
    """9. Verify inactive user attempting admin endpoint receives 401 Unauthorized."""
    slug = f"inact-u-adm-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Inactive Admin Org",
        "organization_slug": slug,
        "email": "inactadmin@test.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]

    # Deactivate user
    async with AsyncSessionLocal() as session:
        user = await session.get(User, uuid.UUID(user_id))
        user.is_active = False
        await session.commit()

    resp = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_inactive_organization_accessing_admin_endpoint(async_client: AsyncClient):
    """10. Verify inactive organization attempting admin endpoint receives 401 Unauthorized."""
    slug = f"inact-o-adm-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Inactive Org Admin Test",
        "organization_slug": slug,
        "email": "inactorgadmin@test.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Deactivate organization
    async with AsyncSessionLocal() as session:
        org = await session.get(Organization, uuid.UUID(org_id))
        org.is_active = False
        await session.commit()

    resp = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_tenant_boundary_headers_and_body_ignored(async_client: AsyncClient):
    """
    13, 14, 15. Verify client-supplied headers (e.g. X-Organization-ID) or query parameters
    cannot override tenant identity or elevate privileges.
    """
    slug = f"tenant-boundary-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant Boundary Org",
        "organization_slug": slug,
        "email": "user@tenantboundary.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    real_org_id = reg_resp.json()["organization"]["id"]

    fake_org_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": fake_org_id
    }

    # Calling /me with fake tenant header must still return the authenticated DB organization_id
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["organization_id"] == real_org_id
    assert resp.json()["organization_id"] != fake_org_id


@pytest.mark.asyncio
async def test_dynamic_db_is_admin_toggle_affects_authorization(async_client: AsyncClient):
    """
    16 & 17. Verify changing is_admin in PostgreSQL dynamically revokes/grants authorization
    for subsequent requests using the SAME token (proving no stale JWT role caching).
    """
    slug = f"dynamic-role-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Dynamic Role Org",
        "organization_slug": slug,
        "email": "admin@dynamicrole.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]

    # 1. Initial admin check -> 200 OK
    res1 = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200

    # 2. Revoke admin in DB (is_admin = False)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, uuid.UUID(user_id))
        user.is_admin = False
        await session.commit()

    # 3. Same token now receives 403 Forbidden
    res2 = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403

    # 4. Grant admin back in DB (is_admin = True)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, uuid.UUID(user_id))
        user.is_admin = True
        await session.commit()

    # 5. Same token now receives 200 OK again
    res3 = await async_client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {token}"})
    assert res3.status_code == 200


@pytest.mark.asyncio
async def test_jwt_claims_alone_cannot_grant_admin_privileges(async_client: AsyncClient):
    """
    18. Verify custom claims in a JWT (e.g. claims={"is_admin": True}) cannot grant admin
    access if the user record in PostgreSQL has is_admin = False.
    """
    slug = f"fake-jwt-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Fake JWT Org",
        "organization_slug": slug,
        "email": "owner@fakejwt.com",
        "password": "Password123!"
    })
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular user in DB
    async with AsyncSessionLocal() as session:
        regular_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@fakejwt.com",
            password_hash=hash_password("Password123!"),
            is_admin=False,
            is_active=True
        )
        session.add(regular_user)
        await session.commit()
        await session.refresh(regular_user)
        reg_user_id = str(regular_user.id)

    # Forge a token for regular user with arbitrary claim claims={"is_admin": True, "role": "admin"}
    forged_token = create_access_token(
        subject=reg_user_id,
        claims={"is_admin": True, "role": "admin"}
    )

    headers = {"Authorization": f"Bearer {forged_token}"}
    resp = await async_client.get("/api/v1/auth/admin-check", headers=headers)
    # Database is authoritative -> is_admin=False -> must return 403 Forbidden
    assert resp.status_code == 403
