import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.project import Project, Approval, Milestone
from app.models.user import User, Role
from app.models.enums import ProjectStageEnum
from app.core.security import create_access_token
from app.services.delay_engine import evaluate_project_delays

STAGE_ORDER = [
  'Proposal',
  'Verification',
  'Survey',
  'Notification',
  'Award',
  'Compensation',
  'Possession',
  'Rehabilitation & Resettlement',
  'Completed',
]


@pytest.mark.asyncio
async def test_unauthenticated_workflow_transition_rejected(async_client: AsyncClient):
    """Unauthenticated workflow transition request must return 401."""
    res = await async_client.post(
        "/api/projects/proj-101/workflow/transition",
        json={"target_stage": "VERIFICATION"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_viewer_role_workflow_mutation_denied(async_client: AsyncClient, admin_token_headers: dict):
    """Viewer role must be denied workflow mutations (403 Forbidden)."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project = proj_res.json()["items"][0]
    project_id = project["id"]

    # Retrieve or create genuine VIEWER user in DB
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User).join(User.role).where(Role.name == "VIEWER")
        )
        viewer_user = res.scalars().first()
        if not viewer_user:
            r_res = await session.execute(select(Role).where(Role.name == "VIEWER"))
            v_role = r_res.scalar_one_or_none()
            if not v_role:
                v_role = Role(name="VIEWER", description="Read Only")
                session.add(v_role)
                await session.flush()
            viewer_user = User(
                name="Test Viewer User",
                email="test.viewer.wf@lams.gov.in",
                role_id=v_role.id,
                is_active=True,
            )
            session.add(viewer_user)
            await session.commit()
            await session.refresh(viewer_user)

        viewer_user_id = viewer_user.id
        db_proj = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if db_proj:
            db_proj.current_stage = ProjectStageEnum.COMPENSATION
        await session.execute(delete(Approval).where(Approval.project_id == project_id))
        await session.commit()

    viewer_token = create_access_token(subject=viewer_user_id, role="VIEWER")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    res = await async_client.post(
        f"/api/projects/{project_id}/workflow/transition",
        json={"target_stage": "Possession"},
        headers=viewer_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_valid_sequential_workflow_transition(async_client: AsyncClient, admin_token_headers: dict):
    """Test valid sequential stage transition (COMPENSATION -> POSSESSION)."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project = proj_res.json()["items"][0]
    project_id = project["id"]

    # Reset project stage & clear pending approvals for test isolation
    async with AsyncSessionLocal() as session:
        db_proj = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if db_proj:
            db_proj.current_stage = ProjectStageEnum.COMPENSATION
        await session.execute(delete(Approval).where(Approval.project_id == project_id))
        await session.commit()

    res = await async_client.post(
        f"/api/projects/{project_id}/workflow/transition",
        json={"target_stage": "Possession", "remarks": "Transition to Possession verified."},
        headers=admin_token_headers,
    )
    assert res.status_code in [200, 201]
    data = res.json()
    assert data["status"] in ["APPROVED", "PENDING_APPROVAL"]


@pytest.mark.asyncio
async def test_reject_skipped_stage_transition(async_client: AsyncClient, admin_token_headers: dict):
    """Test rejecting skipped stage progression (COMPENSATION -> COMPLETED)."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    # Reset project stage & clear pending approvals for test isolation
    async with AsyncSessionLocal() as session:
        db_proj = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if db_proj:
            db_proj.current_stage = ProjectStageEnum.COMPENSATION
        await session.execute(delete(Approval).where(Approval.project_id == project_id))
        await session.commit()

    res = await async_client.post(
        f"/api/projects/{project_id}/workflow/transition",
        json={"target_stage": "Completed", "is_override": False},
        headers=admin_token_headers,
    )
    assert res.status_code == 400
    assert "Cannot skip stages" in res.json()["detail"]


@pytest.mark.asyncio
async def test_reject_backward_stage_transition(async_client: AsyncClient, admin_token_headers: dict):
    """Test rejecting backward stage transition."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    # Reset project stage to COMPENSATION
    async with AsyncSessionLocal() as session:
        db_proj = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if db_proj:
            db_proj.current_stage = ProjectStageEnum.COMPENSATION
        await session.execute(delete(Approval).where(Approval.project_id == project_id))
        await session.commit()

    res = await async_client.post(
        f"/api/projects/{project_id}/workflow/transition",
        json={"target_stage": "PROPOSAL", "is_override": False},
        headers=admin_token_headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_approval_and_rejection_workflow(async_client: AsyncClient, admin_token_headers: dict):
    """Test creating an approval, rejecting it (requiring remarks), and duplicate approval protection."""
    async with AsyncSessionLocal() as session:
        proj = (await session.execute(select(Project))).scalars().first()
        project_id = proj.id

        # Clear existing approvals
        await session.execute(delete(Approval).where(Approval.project_id == project_id))

        # Insert a pending approval record directly
        appr = Approval(
            project_id=project_id,
            stage="Possession",
            requested_by="Field Officer Test",
            status="PENDING",
            remarks="Test approval submission",
        )
        session.add(appr)
        await session.commit()
        await session.refresh(appr)
        appr_id = appr.id

    # 1. Reject approval without remarks should fail (400)
    rej_fail = await async_client.post(
        f"/api/projects/{project_id}/workflow/reject/{appr_id}",
        json={"remarks": ""},
        headers=admin_token_headers,
    )
    assert rej_fail.status_code == 400

    # 2. Reject approval with remarks should succeed (200)
    rej_res = await async_client.post(
        f"/api/projects/{project_id}/workflow/reject/{appr_id}",
        json={"remarks": "Boundary survey map incomplete."},
        headers=admin_token_headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

    # 3. Attempting to approve an ALREADY REJECTED request should fail (409 Conflict)
    dup_appr = await async_client.post(
        f"/api/projects/{project_id}/workflow/approve/{appr_id}",
        json={"remarks": "Attempting duplicate approval"},
        headers=admin_token_headers,
    )
    assert dup_appr.status_code == 409


@pytest.mark.asyncio
async def test_delay_detection_engine(async_client: AsyncClient, admin_token_headers: dict):
    """Test milestone delay detection engine calculates delay_days and updates project status."""
    async with AsyncSessionLocal() as session:
        proj = (await session.execute(select(Project))).scalars().first()
        project_id = proj.id

        # Create an overdue milestone
        past_date = date.today() - timedelta(days=40)
        ms = Milestone(
            project_id=project_id,
            title="Gazette Notification 20A Publication",
            stage="Notification",
            planned_date=past_date,
            actual_date=None,
        )
        session.add(ms)
        await session.commit()

        # Run delay engine
        max_delay, new_status = await evaluate_project_delays(session, project_id)
        await session.commit()

        assert max_delay >= 40
        assert new_status.value == "CRITICAL"


@pytest.mark.asyncio
async def test_workflow_history_endpoint(async_client: AsyncClient, admin_token_headers: dict):
    """Test GET /api/projects/{project_id}/workflow/history."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    res = await async_client.get(f"/api/projects/{project_id}/workflow/history", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "current_stage" in data
    assert "status" in data
    assert "history" in data


@pytest.mark.asyncio
async def test_notification_filtering_and_read_endpoints(async_client: AsyncClient, admin_token_headers: dict):
    """Test notification list filtering, unread count, mark read, and mark all read."""
    # List notifications
    res = await async_client.get("/api/notifications", headers=admin_token_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0

    # Mark all read
    read_all = await async_client.put("/api/notifications/read-all", headers=admin_token_headers)
    assert read_all.status_code == 200

    # Check unread count is 0
    cnt_res = await async_client.get("/api/notifications/unread-count", headers=admin_token_headers)
    assert cnt_res.status_code == 200
    assert cnt_res.json()["unread_count"] == 0

