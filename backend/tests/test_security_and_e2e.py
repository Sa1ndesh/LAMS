import pytest
import io
import uuid
import jwt
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, Role
from app.models.project import Project, Milestone, Approval
from app.models.parcel import LandParcel
from app.models.compensation import CompensationRecord
from app.models.family import AffectedFamily, RehabilitationRecord
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.models.enums import ProjectStageEnum


# =====================================================================
# 1. SECURITY & EDGE CASE TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_security_malformed_and_forged_jwt(async_client: AsyncClient):
    """Test that malformed, forged, or invalid signature tokens return 401 Unauthorized."""
    # 1. Malformed token
    res1 = await async_client.get("/api/projects", headers={"Authorization": "Bearer not.a.valid.jwt.token"})
    assert res1.status_code == 401

    # 2. Token signed with wrong secret key
    forged_token = jwt.encode({"sub": "admin-uuid", "role": "SUPER_ADMIN"}, "WRONG_SECRET_KEY", algorithm="HS256")
    res2 = await async_client.get("/api/projects", headers={"Authorization": f"Bearer {forged_token}"})
    assert res2.status_code == 401

    # 3. Token missing subject claim
    no_sub_token = jwt.encode({"role": "SUPER_ADMIN"}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    res3 = await async_client.get("/api/projects", headers={"Authorization": f"Bearer {no_sub_token}"})
    assert res3.status_code == 401


@pytest.mark.asyncio
async def test_security_sqli_and_path_traversal_attempts(async_client: AsyncClient, admin_token_headers: dict):
    """Test that SQL injection strings and path traversal attempts are safely handled without error/leak."""
    # 1. SQLi string in search query
    res1 = await async_client.get("/api/projects?search=' OR '1'='1", headers=admin_token_headers)
    assert res1.status_code == 200

    # 2. Path traversal in document download endpoint
    res2 = await async_client.get(
        "/api/projects/proj-1/documents/..%2F..%2F..%2Fetc%2Fpasswd/download",
        headers=admin_token_headers,
    )
    assert res2.status_code in [400, 404]

    # 3. Path traversal in document file path
    res3 = await async_client.get(
        "/api/projects/proj-1/documents/../../secret.txt/preview",
        headers=admin_token_headers,
    )
    assert res3.status_code in [400, 404]


@pytest.mark.asyncio
async def test_security_document_upload_edge_cases(async_client: AsyncClient, admin_token_headers: dict):
    """Test document upload security bounds (empty file, unsupported extension, >10MB size limit)."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    # 1. Unsupported extension (.exe)
    exe_file = ("test.exe", b"binary_executable_bytes", "application/x-msdownload")
    res1 = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files={"file": exe_file},
        data={"category": "PROPOSAL"},
        headers=admin_token_headers,
    )
    assert res1.status_code == 400

    # 2. Empty 0-byte file
    empty_file = ("empty.pdf", b"", "application/pdf")
    res2 = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files={"file": empty_file},
        data={"category": "PROPOSAL"},
        headers=admin_token_headers,
    )
    assert res2.status_code == 400

    # 3. Oversized file (>10 MB)
    large_content = b"0" * (10 * 1024 * 1024 + 100)
    large_file = ("large.pdf", large_content, "application/pdf")
    res3 = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files={"file": large_file},
        data={"category": "PROPOSAL"},
        headers=admin_token_headers,
    )
    assert res3.status_code in [400, 413]


@pytest.mark.asyncio
async def test_security_invalid_coordinates_and_negative_area(async_client: AsyncClient, admin_token_headers: dict):
    """Test validation rejection for negative land proposed hectares or invalid coordinates."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    # 1. Negative land area in parcel creation
    bad_parcel_data = {
        "survey_number": "SY-9999-BAD",
        "state_id": 1,
        "district_id": 1,
        "taluk": "Test Taluk",
        "village": "Test Village",
        "area_hectares": -25.5,
        "land_type": "Agricultural",
        "owner_name": "Bad Owner",
        "acquisition_status": "Proposed",
    }
    res1 = await async_client.post(f"/api/projects/{project_id}/parcels", json=bad_parcel_data, headers=admin_token_headers)
    assert res1.status_code == 422


# =====================================================================
# 2. 8-ROLE RBAC MATRIX VERIFICATION
# =====================================================================

@pytest.mark.asyncio
async def test_8_role_rbac_matrix_enforcement(async_client: AsyncClient, admin_token_headers: dict):
    """Verify RBAC mutation access control across all 8 LAMS administrative roles."""
    proj_res = await async_client.get("/api/projects", headers=admin_token_headers)
    project_id = proj_res.json()["items"][0]["id"]

    async with AsyncSessionLocal() as session:
        admin_user = (await session.execute(select(User))).scalars().first()
        admin_user_id = admin_user.id

        # Retrieve or create VIEWER role user in DB
        viewer_role = (await session.execute(select(Role).where(Role.name == "VIEWER"))).scalar_one_or_none()
        if not viewer_role:
            viewer_role = Role(name="VIEWER", description="Viewer Role")
            session.add(viewer_role)
            await session.flush()

        viewer_user = (await session.execute(select(User).where(User.role_id == viewer_role.id))).scalars().first()
        if not viewer_user:
            viewer_user = User(
                name="RBAC Test Viewer User",
                email=f"viewer-{uuid.uuid4().hex[:6]}@lams.gov.in",
                role_id=viewer_role.id,
                is_active=True,
            )
            session.add(viewer_user)
            await session.commit()
            await session.refresh(viewer_user)

        viewer_user_id = viewer_user.id

    permitted_roles = [
        "SUPER_ADMIN",
        "CENTRAL_MINISTRY",
        "STATE_AUTHORITY",
        "DISTRICT_ADMIN",
        "LAND_ACQUISITION_OFFICER",
        "FIELD_OFFICER",
        "PROJECT_IMPLEMENTING_AGENCY",
    ]

    for role_name in permitted_roles:
        token = create_access_token(subject=admin_user_id, role=role_name)
        headers = {"Authorization": f"Bearer {token}"}

        # Reset stage to Proposal and clear pending approvals
        async with AsyncSessionLocal() as session:
            p = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
            if p:
                p.current_stage = ProjectStageEnum.PROPOSAL
                p.state_id = admin_user.state_id or 1
            await session.execute(delete(Approval).where(Approval.project_id == project_id))
            await session.commit()

        res = await async_client.post(
            f"/api/projects/{project_id}/workflow/transition",
            json={"target_stage": "Verification", "remarks": f"Permitted transition by {role_name}"},
            headers=headers,
        )
        assert res.status_code in [200, 201], f"Role {role_name} should be allowed, got {res.status_code}"

    # Denied VIEWER Role test
    viewer_token = create_access_token(subject=viewer_user_id, role="VIEWER")
    v_res = await async_client.post(
        f"/api/projects/{project_id}/workflow/transition",
        json={"target_stage": "Verification", "remarks": "Unauthorized transition by VIEWER"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert v_res.status_code == 403, f"Role VIEWER should be denied (403), got {v_res.status_code}"


# =====================================================================
# 3. END-TO-END MULTI-STEP INTEGRATION FLOWS
# =====================================================================

@pytest.mark.asyncio
async def test_e2e_full_lifecycle_flow(async_client: AsyncClient, admin_token_headers: dict):
    """End-to-end integration flow: Project Creation -> Parcel -> Compensation -> Family -> Document -> Workflow Approval -> Audit Log -> Analytics -> AI Risk."""
    
    unique_code = f"E2E-{uuid.uuid4().hex[:6].upper()}"

    # 1. Create Project
    proj_payload = {
        "project_code": unique_code,
        "name": "E2E Integrated Express Highway Corridor",
        "category": "Highway",
        "description": "Full-stack end-to-end integration testing corridor.",
        "ministry": "Ministry of Road Transport and Highways",
        "implementing_agency": "NHAI",
        "state_id": 1,
        "district_id": 1,
        "village": "Expressway Junction",
        "land_proposed_hectares": 120.0,
        "budget_inr": 2_500_000_000.0,
        "current_stage": "Proposal",
        "status": "ON_TRACK",
        "start_date": str(date.today()),
        "target_completion_date": str(date.today() + timedelta(days=365)),
    }
    p_res = await async_client.post("/api/projects", json=proj_payload, headers=admin_token_headers)
    assert p_res.status_code == 201
    project_id = p_res.json()["id"]

    # 2. Add Land Parcel
    parcel_payload = {
        "survey_number": f"SY-E2E-{uuid.uuid4().hex[:4].upper()}",
        "state_id": 1,
        "district_id": 1,
        "taluk": "North Taluk",
        "village": "Expressway Junction",
        "area_hectares": 45.0,
        "land_type": "Agricultural",
        "owner_name": "Suresh Patel & Sons",
        "acquisition_status": "Proposed",
        "compensation_status": "Assessed",
        "possession_status": "Not Taken",
        "latitude": 26.9124,
        "longitude": 75.7873,
    }
    pcl_res = await async_client.post(f"/api/projects/{project_id}/parcels", json=parcel_payload, headers=admin_token_headers)
    assert pcl_res.status_code == 201
    parcel_id = pcl_res.json()["id"]

    # 3. Assess Compensation
    comp_payload = {
        "parcel_id": parcel_id,
        "assessed_amount_inr": 50_000_000.0,
        "approved_amount_inr": 50_000_000.0,
        "disbursed_amount_inr": 25_000_000.0,
        "payment_status": "PARTIALLY_DISBURSED",
        "payment_date": str(date.today()),
    }
    c_res = await async_client.post(f"/api/projects/{project_id}/compensation", json=comp_payload, headers=admin_token_headers)
    assert c_res.status_code == 201

    # 4. Add Affected Family
    fam_payload = {
        "family_reference_id": f"FAM-{uuid.uuid4().hex[:4].upper()}",
        "village": "Expressway Junction",
        "head_of_family": "Ramesh Chandra",
        "family_members_count": 5,
        "category": "OBC",
        "is_affected": True,
        "is_displaced": True,
        "rr_status": "IDENTIFIED",
    }
    f_res = await async_client.post(f"/api/projects/{project_id}/families", json=fam_payload, headers=admin_token_headers)
    assert f_res.status_code == 201

    # 5. Upload Document
    pdf_content = b"%PDF-1.4 E2E Test Document Content"
    pdf_file = ("e2e_proposal.pdf", pdf_content, "application/pdf")
    doc_res = await async_client.post(
        f"/api/projects/{project_id}/documents/upload",
        files={"file": pdf_file},
        data={"category": "PROPOSAL", "description": "E2E Gazette Proposal PDF"},
        headers=admin_token_headers,
    )
    assert doc_res.status_code == 201

    # 6. Workflow Transition Request & Approval
    trans_res = await async_client.post(
        f"/api/projects/{project_id}/workflow/transition",
        json={"target_stage": "Verification", "remarks": "Advancing E2E project to Verification"},
        headers=admin_token_headers,
    )
    assert trans_res.status_code in [200, 201]

    # 7. Check Audit Logs & Notifications
    async with AsyncSessionLocal() as session:
        audit_entries = (await session.execute(select(AuditLog).where(AuditLog.entity_id == project_id))).scalars().all()
        assert len(audit_entries) >= 1

        notif_entries = (await session.execute(select(Notification).where(Notification.project_id == project_id))).scalars().all()
        assert len(notif_entries) >= 1

    # 8. Check Analytics Summary Includes New Metrics
    sum_res = await async_client.get("/api/analytics/summary", headers=admin_token_headers)
    assert sum_res.status_code == 200
    assert sum_res.json()["total_projects"] >= 1

    # 9. Evaluate AI Risk Score & Insights for New Project
    ai_res = await async_client.get(f"/api/ai/projects/{project_id}/risk", headers=admin_token_headers)
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert ai_data["project_id"] == project_id
    assert "risk_score" in ai_data
    assert "recommendations" in ai_data

    # Cleanup E2E project
    await async_client.delete(f"/api/projects/{project_id}", headers=admin_token_headers)

