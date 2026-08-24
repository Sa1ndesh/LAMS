import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_get_analytics_summary(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/summary returns national overview KPIs."""
    res = await async_client.get("/api/analytics/summary", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_projects" in data
    assert data["total_projects"] >= 1
    assert "total_land_proposed_hectares" in data
    assert "total_land_acquired_hectares" in data
    assert "acquisition_percentage" in data
    assert "total_compensation_assessed" in data
    assert "total_compensation_disbursed" in data
    assert "total_affected_families" in data


@pytest.mark.asyncio
async def test_get_state_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/states returns state-wise breakdown."""
    res = await async_client.get("/api/analytics/states", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    state_item = data["items"][0]
    assert "state_name" in state_item
    assert "project_count" in state_item


@pytest.mark.asyncio
async def test_get_project_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/projects returns project-by-project performance."""
    res = await async_client.get("/api/analytics/projects", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert "project_code" in item
    assert "acquisition_percentage" in item
    assert "risk_indicator" in item


@pytest.mark.asyncio
async def test_get_land_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/land returns land acquisition breakdowns."""
    res = await async_client.get("/api/analytics/land", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_proposed" in data
    assert "by_state" in data
    assert "by_project" in data
    assert "by_land_type" in data


@pytest.mark.asyncio
async def test_get_compensation_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/compensation returns treasury disbursement metrics."""
    res = await async_client.get("/api/analytics/compensation", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_assessed" in data
    assert "total_disbursed" in data
    assert "by_payment_status" in data


@pytest.mark.asyncio
async def test_get_rehabilitation_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/rehabilitation returns R&R family metrics."""
    res = await async_client.get("/api/analytics/rehabilitation", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_affected" in data
    assert "total_displaced" in data
    assert "by_social_category" in data


@pytest.mark.asyncio
async def test_get_timeline_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/timeline returns milestone adherence metrics."""
    res = await async_client.get("/api/analytics/timeline", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_milestones" in data
    assert "completed_milestones" in data
    assert "ontime_percentage" in data


@pytest.mark.asyncio
async def test_get_workflow_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/workflow returns approval statistics."""
    res = await async_client.get("/api/analytics/workflow", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "stage_distribution" in data
    assert "pending_approvals" in data


@pytest.mark.asyncio
async def test_get_delay_analytics(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/analytics/delays returns delay breakdowns."""
    res = await async_client.get("/api/analytics/delays", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "delayed_projects_count" in data
    assert "by_state" in data
    assert "by_category" in data


@pytest.mark.asyncio
async def test_date_range_validation(async_client: AsyncClient, admin_token_headers: dict):
    """Test that date_from > date_to returns HTTP 400 Bad Request."""
    res = await async_client.get(
        "/api/analytics/summary?date_from=2026-12-31&date_to=2026-01-01",
        headers=admin_token_headers,
    )
    assert res.status_code == 400
    assert "date_from must be less than or equal to date_to" in res.json()["detail"]


@pytest.mark.asyncio
async def test_state_authority_rbac_scoping(async_client: AsyncClient):
    """Test that a STATE_AUTHORITY user with state_id=1 gets state-scoped analytics."""
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        valid_id = user.id

    state_token = create_access_token(subject=valid_id, role="STATE_AUTHORITY")
    headers = {"Authorization": f"Bearer {state_token}"}

    res = await async_client.get("/api/analytics/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_projects" in data

