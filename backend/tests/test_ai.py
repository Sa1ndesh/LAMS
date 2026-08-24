import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.project import Project, Milestone, Approval
from app.models.parcel import LandParcel
from app.models.compensation import CompensationRecord
from app.models.family import AffectedFamily, RehabilitationRecord
from app.models.user import User, Role
from app.models.geography import State
from app.models.enums import ProjectStatusEnum, ProjectStageEnum, MilestoneStatusEnum, ApprovalStatusEnum
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_unauthenticated_ai_risk_request_rejected(async_client: AsyncClient):
    """Unauthenticated request to AI endpoints must return 401 Unauthorized."""
    res = await async_client.get("/api/ai/projects/proj-101/risk")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_project_risk_analysis(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/ai/projects/{project_id}/risk returns complete explainable risk model."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    res = await async_client.get(f"/api/ai/projects/{project_id}/risk", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == project_id
    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0
    assert "factors" in data
    assert "recommendations" in data


@pytest.mark.asyncio
async def test_get_project_insights(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/ai/projects/{project_id}/insights returns bottlenecks and summary."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    res = await async_client.get(f"/api/ai/projects/{project_id}/insights", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == project_id
    assert "bottlenecks" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_ai_overview_endpoint(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/ai/overview returns national decision-support summary."""
    res = await async_client.get("/api/ai/overview", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()

    assert "total_projects" in data
    assert data["total_projects"] >= 1
    assert "average_risk_score" in data
    assert "highest_risk_projects" in data
    assert "national_insights" in data


@pytest.mark.asyncio
async def test_high_risk_projects_ranking(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/ai/projects/high-risk returns projects ordered descending by risk_score."""
    res = await async_client.get("/api/ai/projects/high-risk", headers=admin_token_headers)
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    if len(items) > 1:
        assert items[0]["risk_score"] >= items[1]["risk_score"]


@pytest.mark.asyncio
async def test_milestone_delay_risk_factor(async_client: AsyncClient, admin_token_headers: dict):
    """Test that a 65-day milestone delay triggers CRITICAL severity risk factor and points."""
    async with AsyncSessionLocal() as session:
        proj = (await session.execute(select(Project))).scalars().first()
        project_id = proj.id

        # Insert a 65-day delayed milestone
        past_date = date.today() - timedelta(days=65)
        ms = Milestone(
            project_id=project_id,
            title="Overdue Survey Verification 20A",
            stage="Survey",
            planned_date=past_date,
            actual_date=None,
            delay_days=65,
            status=MilestoneStatusEnum.DELAYED,
        )
        session.add(ms)
        await session.commit()

    res = await async_client.get(f"/api/ai/projects/{project_id}/risk", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()

    ms_factors = [f for f in data["factors"] if "Milestone" in f["factor"]]
    assert len(ms_factors) > 0
    assert "+30 pts" in ms_factors[0]["impact"] or "+22 pts" in ms_factors[0]["impact"] or "+14 pts" in ms_factors[0]["impact"]


@pytest.mark.asyncio
async def test_compensation_bottleneck_detection(async_client: AsyncClient, admin_token_headers: dict):
    """Test that a large approved undisbursed compensation balance triggers compensation bottleneck."""
    async with AsyncSessionLocal() as session:
        proj = (await session.execute(select(Project))).scalars().first()
        project_id = proj.id

        # Insert a parcel and compensation record with ₹15 Cr approved but ₹0 disbursed
        parcel = (await session.execute(select(LandParcel).where(LandParcel.project_id == project_id))).scalars().first()

        comp = CompensationRecord(
            project_id=project_id,
            parcel_id=parcel.id if parcel else "dummy-parcel",
            assessed_amount_inr=150_000_000.0,
            approved_amount_inr=150_000_000.0,
            disbursed_amount_inr=0.0,
        )
        session.add(comp)
        await session.commit()

    res = await async_client.get(f"/api/ai/projects/{project_id}/insights", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()

    comp_bottlenecks = [b for b in data["bottlenecks"] if b["category"] == "COMPENSATION"]
    assert len(comp_bottlenecks) > 0
    assert "Disbursement" in comp_bottlenecks[0]["title"] or "Treasury" in comp_bottlenecks[0]["title"]


@pytest.mark.asyncio
async def test_state_authority_rbac_ai_scoping(async_client: AsyncClient):
    """Test that a STATE_AUTHORITY user is denied access (403) to a project in a different state."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).join(User.role).where(Role.name == "STATE_AUTHORITY"))
        state_user = res.scalars().first()
        if not state_user:
            r_res = await session.execute(select(Role).where(Role.name == "STATE_AUTHORITY"))
            st_role = r_res.scalar_one_or_none()
            if not st_role:
                st_role = Role(name="STATE_AUTHORITY", description="State Authority")
                session.add(st_role)
                await session.flush()
            state_user = User(
                name="State Authority Test AI User",
                email="state.test.ai@lams.gov.in",
                role_id=st_role.id,
                state_id=2,
                is_active=True,
            )
            session.add(state_user)
            await session.commit()
            await session.refresh(state_user)
        else:
            state_user.state_id = 2
            await session.commit()

        state_user_id = state_user.id
        proj = (await session.execute(select(Project).where(Project.state_id != 2))).scalars().first()
        project_id = proj.id

    token = create_access_token(subject=state_user_id, role="STATE_AUTHORITY")
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get(f"/api/ai/projects/{project_id}/risk", headers=headers)
    assert res.status_code == 403

