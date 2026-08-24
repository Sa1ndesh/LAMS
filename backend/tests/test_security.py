import pytest
import io
import uuid
import jwt
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, Role
from app.models.project import Project, Approval
from app.models.geography import State
from app.models.enums import ProjectStageEnum


# =====================================================================
# 1. AUTHENTICATION & JWT SECURITY
# =====================================================================

@pytest.mark.asyncio
async def test_auth_security_invalid_password_and_email(async_client: AsyncClient):
    """Verify login failures use generic error messages without exposing user existence."""
    res1 = await async_client.post(
        "/api/auth/login",
        json={"email": "nonexistent@lams.gov.in", "password": "WrongPassword123"},
    )
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json()["detail"]

    res2 = await async_client.post(
        "/api/auth/login",
        json={"email": settings.SEED_ADMIN_EMAIL, "password": "WrongPassword123"},
    )
    assert res2.status_code == 401
    assert "Invalid email or password" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_auth_security_inactive_user_blocked(async_client: AsyncClient):
    """Verify inactive users are denied authentication access."""
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        valid_user_id = user.id
        # Temporarily deactivate user
        user.is_active = False
        await session.commit()

    token = create_access_token(subject=valid_user_id, role="SUPER_ADMIN")
    res = await async_client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert "inactive" in res.json()["detail"].lower()

    # Re-activate user
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.id == valid_user_id))).scalar_one()
        u.is_active = True
        await session.commit()


# =====================================================================
# 2. IDOR / BOLA SPATIAL BOUNDARY ISOLATION
# =====================================================================

@pytest.mark.asyncio
async def test_idor_spatial_boundary_isolation(async_client: AsyncClient):
    """Verify STATE_AUTHORITY user cannot access project details in another state (IDOR/BOLA prevention)."""
    async with AsyncSessionLocal() as session:
        # Fetch two projects in different states if available
        p1 = (await session.execute(select(Project))).scalars().first()
        proj_1_id = p1.id
        proj_1_state_id = p1.state_id

        # Get all valid states from DB
        all_states = (await session.execute(select(State))).scalars().all()
        user_state_id = all_states[0].id if all_states else 1
        target_state_id = all_states[1].id if len(all_states) > 1 else user_state_id + 1

        state_role = (await session.execute(select(Role).where(Role.name == "STATE_AUTHORITY"))).scalar_one()
        st_user = User(
            name="IDOR State User Test",
            email=f"idor-state-{uuid.uuid4().hex[:6]}@lams.gov.in",
            role_id=state_role.id,
            state_id=user_state_id,
            is_active=True,
        )
        session.add(st_user)
        await session.commit()
        await session.refresh(st_user)
        st_user_id = st_user.id

        # Set project to a different valid state_id
        proj_1_id = p1.id
        p1.state_id = target_state_id
        await session.commit()

    token = create_access_token(subject=st_user_id, role="STATE_AUTHORITY")
    headers = {"Authorization": f"Bearer {token}"}

    # Attempting to fetch project in a different state should return 403 Forbidden
    res = await async_client.get(f"/api/projects/{proj_1_id}", headers=headers)

    # Restore project state_id
    async with AsyncSessionLocal() as session:
        p = (await session.execute(select(Project).where(Project.id == proj_1_id))).scalar_one()
        p.state_id = proj_1_state_id
        await session.commit()

    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


# =====================================================================
# 3. SECURITY HEADERS VERIFICATION
# =====================================================================

@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    """Verify production security headers are set on HTTP responses."""
    res = await async_client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# =====================================================================
# 4. XSS & PAYLOAD SANITIZATION
# =====================================================================

@pytest.mark.asyncio
async def test_xss_script_payload_safety(async_client: AsyncClient, admin_token_headers: dict):
    """Verify HTML/JS script injection strings are stored safely without execution or syntax failure."""
    xss_payload = {
        "project_code": f"XSS-{date.today().strftime('%Y%m%d%H%M%S')}",
        "name": "<script>alert('XSS')</script> Highway Project",
        "category": "Highway",
        "description": "<img src=x onerror=alert('XSS')>",
        "ministry": "Ministry of Transport",
        "implementing_agency": "NHAI",
        "state_id": 1,
        "district_id": 1,
        "village": "<svg/onload=alert('XSS')>",
        "land_proposed_hectares": 50.0,
        "budget_inr": 100_000_000.0,
        "current_stage": "Proposal",
        "status": "ON_TRACK",
        "start_date": str(date.today()),
        "target_completion_date": str(date.today() + timedelta(days=300)),
    }

    res = await async_client.post("/api/projects", json=xss_payload, headers=admin_token_headers)
    assert res.status_code == 201
    data = res.json()

    # Clean text response string preserved as literal text
    assert "<script>alert('XSS')</script>" in data["name"]
    assert "<img src=x onerror=alert('XSS')>" in data["description"]

    # Cleanup project
    await async_client.delete(f"/api/projects/{data['id']}", headers=admin_token_headers)
