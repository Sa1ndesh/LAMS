import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token


@pytest_asyncio.fixture
async def seeded_admin_user():
    """Fetches seeded SUPER_ADMIN user from database."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User).where(User.email == "admin.national@lams.gov.in").options(selectinload(User.role))
        )
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def seeded_viewer_user():
    """Fetches or creates a test VIEWER user in database."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User).where(User.email == "survey.field@lams.gov.in").options(selectinload(User.role))
        )
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def admin_token(seeded_admin_user):
    """Generates valid SUPER_ADMIN bearer token for API testing."""
    if seeded_admin_user:
        return create_access_token(subject=seeded_admin_user.id, role="SUPER_ADMIN")
    return create_access_token(subject="admin-test-uuid", role="SUPER_ADMIN")


@pytest_asyncio.fixture
async def viewer_token(seeded_viewer_user):
    """Generates valid VIEWER bearer token for API testing."""
    if seeded_viewer_user:
        return create_access_token(subject=seeded_viewer_user.id, role="FIELD_OFFICER")
    return create_access_token(subject="viewer-test-uuid", role="VIEWER")


@pytest.mark.asyncio
async def test_dashboard_summary_api(admin_token):
    """Test GET /api/dashboard/summary."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/dashboard/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        assert "land_proposed_hectares" in data
        assert "acquisition_percentage" in data
        assert "state_progress" in data


@pytest.mark.asyncio
async def test_list_projects_api(admin_token):
    """Test GET /api/projects."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/projects", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data


@pytest.mark.asyncio
async def test_create_project_permission_denied_for_viewer(viewer_token):
    """Test that non-admin role is denied from POST /api/projects with HTTP 403."""
    headers = {"Authorization": f"Bearer {viewer_token}"}
    payload = {
        "project_code": "TEST-PROJ-999",
        "name": "Unauthorized Project",
        "category": "Highway",
        "ministry": "Ministry of Transport",
        "implementing_agency": "NHAI",
        "state_id": 1,
        "district_id": 1,
        "village": "Test Village",
        "land_proposed_hectares": 100.0,
        "budget_inr": 100000000.0,
        "start_date": "2026-01-01",
        "target_completion_date": "2027-01-01",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/projects", json=payload, headers=headers)
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_notifications_api(admin_token):
    """Test GET /api/notifications."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "unread_count" in data

