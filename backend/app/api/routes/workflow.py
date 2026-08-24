import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.project import Project, Approval, Milestone
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.models.enums import UserRoleEnum, ProjectStageEnum, ProjectStatusEnum, ApprovalStatusEnum, NotificationTypeEnum
from app.schemas.workflow import (
    WorkflowTransitionRequest,
    ApprovalActionRequest,
    ApprovalResponse,
    ApprovalListResponse,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
)
from app.services.delay_engine import evaluate_project_delays

logger = logging.getLogger("lams.api.workflow")
router = APIRouter(tags=["Workflow & Approvals"])

# Ordered Sequential Stages
STAGE_SEQUENCE = [
    ProjectStageEnum.PROPOSAL,
    ProjectStageEnum.VERIFICATION,
    ProjectStageEnum.SURVEY,
    ProjectStageEnum.NOTIFICATION,
    ProjectStageEnum.AWARD,
    ProjectStageEnum.COMPENSATION,
    ProjectStageEnum.POSSESSION,
    ProjectStageEnum.REHABILITATION,
    ProjectStageEnum.COMPLETED,
]

STAGE_NAME_MAP = {
    "PROPOSAL": ProjectStageEnum.PROPOSAL,
    "VERIFICATION": ProjectStageEnum.VERIFICATION,
    "SURVEY": ProjectStageEnum.SURVEY,
    "NOTIFICATION": ProjectStageEnum.NOTIFICATION,
    "AWARD": ProjectStageEnum.AWARD,
    "COMPENSATION": ProjectStageEnum.COMPENSATION,
    "POSSESSION": ProjectStageEnum.POSSESSION,
    "REHABILITATION": ProjectStageEnum.REHABILITATION,
    "REHABILITATION & RESETTLEMENT": ProjectStageEnum.REHABILITATION,
    "COMPLETED": ProjectStageEnum.COMPLETED,
}


def parse_stage_enum(stage_str: str) -> Optional[ProjectStageEnum]:
    u_str = stage_str.strip().upper()
    if u_str in STAGE_NAME_MAP:
        return STAGE_NAME_MAP[u_str]
    for stage_enum in ProjectStageEnum:
        if stage_enum.value.upper() == u_str or stage_enum.name.upper() == u_str:
            return stage_enum
    return None


def to_approval_response(appr: Approval) -> ApprovalResponse:
    status_str = appr.status.value if hasattr(appr.status, "value") else str(appr.status)
    return ApprovalResponse(
        id=appr.id,
        project_id=appr.project_id,
        stage=appr.stage,
        requested_by=appr.requested_by,
        approved_by=appr.approved_by,
        status=status_str,
        remarks=appr.remarks,
        requested_at=appr.requested_at,
        approved_at=appr.approved_at,
        created_at=appr.created_at,
        updated_at=appr.updated_at,
    )


@router.post("/projects/{project_id}/workflow/transition")
async def transition_project_stage(
    project_id: str,
    payload: WorkflowTransitionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.STATE_AUTHORITY,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
            UserRoleEnum.FIELD_OFFICER,
            UserRoleEnum.PROJECT_IMPLEMENTING_AGENCY,
        )
    ),
):
    """
    Initiates or completes a project lifecycle stage transition.
    Validates sequential stage progression, creates approvals if required, and records AuditLogs & Notifications.
    """
    # 1. Fetch project
    proj_res = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    # 2. Check if project is already completed
    curr_stage_val = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)
    if curr_stage_val == ProjectStageEnum.COMPLETED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project lifecycle is already completed.")

    # 3. Parse target stage
    target_enum = parse_stage_enum(payload.target_stage)
    if not target_enum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid target stage '{payload.target_stage}'.")

    current_enum = parse_stage_enum(curr_stage_val)
    if current_enum == target_enum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Project is already in stage '{target_enum.value}'.")

    # 4. Validate sequential progression
    curr_idx = STAGE_SEQUENCE.index(current_enum) if current_enum in STAGE_SEQUENCE else 0
    target_idx = STAGE_SEQUENCE.index(target_enum) if target_enum in STAGE_SEQUENCE else 0

    user_role_name = current_user.role.name if current_user.role else "VIEWER"
    is_super_admin = user_role_name == "SUPER_ADMIN"

    if target_idx != curr_idx + 1:
        if not (payload.is_override and is_super_admin):
            if target_idx < curr_idx:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backward stage transitions are not permitted.")
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot skip stages. Next sequential stage must be '{STAGE_SEQUENCE[curr_idx + 1].value}'.")

    # 5. Check for existing PENDING approval
    pending_res = await session.execute(
        select(Approval).where(
            Approval.project_id == project_id,
            Approval.status == ApprovalStatusEnum.PENDING,
        )
    )
    if pending_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A pending approval request already exists for this project.")

    # 6. Determine if approval required or direct transition
    # Higher authority roles or direct verification/survey can advance immediately, or create pending approval
    needs_approval = target_enum in [
        ProjectStageEnum.NOTIFICATION,
        ProjectStageEnum.AWARD,
        ProjectStageEnum.COMPENSATION,
        ProjectStageEnum.POSSESSION,
        ProjectStageEnum.REHABILITATION,
        ProjectStageEnum.COMPLETED,
    ] and user_role_name in ["FIELD_OFFICER", "PROJECT_IMPLEMENTING_AGENCY", "LAND_ACQUISITION_OFFICER"] and not is_super_admin

    if needs_approval:
        # Create PENDING Approval Request
        appr = Approval(
            project_id=project_id,
            stage=target_enum.value,
            requested_by=current_user.name,
            status=ApprovalStatusEnum.PENDING,
            remarks=payload.remarks,
            requested_at=datetime.now(timezone.utc),
        )
        session.add(appr)
        await session.flush()

        # Notification
        notif = Notification(
            project_id=project_id,
            notification_type=NotificationTypeEnum.APPROVAL_REQUIRED,
            title=f"Approval Required: {project.name}",
            message=f"Transition to stage '{target_enum.value}' requested by {current_user.name}.",
            is_read=False,
        )
        session.add(notif)

        # AuditLog
        audit = AuditLog(
            user_id=current_user.id,
            entity_type="WORKFLOW",
            entity_id=appr.id,
            action="WORKFLOW_SUBMITTED",
            old_value={"stage": curr_stage_val},
            new_value={"requested_stage": target_enum.value, "approval_id": appr.id},
        )
        session.add(audit)
        await session.commit()
        await session.refresh(appr)

        return {
            "message": f"Stage transition to '{target_enum.value}' submitted for administrative approval.",
            "status": "PENDING_APPROVAL",
            "approval": to_approval_response(appr),
            "project_id": project_id,
            "current_stage": curr_stage_val,
        }
    else:
        # Direct Transition Approved
        old_stage = curr_stage_val
        project.current_stage = target_enum

        # Evaluate delays
        await evaluate_project_delays(session, project_id)

        # Create Auto-Approved Record for History
        appr = Approval(
            project_id=project_id,
            stage=target_enum.value,
            requested_by=current_user.name,
            approved_by=current_user.name,
            status=ApprovalStatusEnum.APPROVED,
            remarks=payload.remarks or "Direct stage transition",
            requested_at=datetime.now(timezone.utc),
            approved_at=datetime.now(timezone.utc),
        )
        session.add(appr)

        # Notification
        notif = Notification(
            project_id=project_id,
            notification_type=NotificationTypeEnum.STAGE_CHANGE,
            title=f"Lifecycle Stage Advanced: {project.name}",
            message=f"Project advanced from '{old_stage}' to '{target_enum.value}' by {current_user.name}.",
            is_read=False,
        )
        session.add(notif)

        # AuditLog
        audit = AuditLog(
            user_id=current_user.id,
            entity_type="WORKFLOW",
            entity_id=project_id,
            action="STAGE_CHANGED",
            old_value={"stage": old_stage},
            new_value={"stage": target_enum.value},
        )
        session.add(audit)
        await session.commit()

        return {
            "message": f"Project successfully advanced to '{target_enum.value}'.",
            "status": "APPROVED",
            "project_id": project_id,
            "previous_stage": old_stage,
            "current_stage": target_enum.value,
        }


@router.post("/projects/{project_id}/workflow/approve/{approval_id}", response_model=ApprovalResponse)
async def approve_workflow_request(
    project_id: str,
    approval_id: str,
    payload: Optional[ApprovalActionRequest] = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.STATE_AUTHORITY,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """
    Approves a pending workflow stage transition request with atomic duplicate approval protection.
    (Viewer role denied).
    """
    # Concurrency Lock / Select Approval
    appr_res = await session.execute(
        select(Approval).where(Approval.id == approval_id, Approval.project_id == project_id)
    )
    appr = appr_res.scalar_one_or_none()
    if not appr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")

    status_str = appr.status.value if hasattr(appr.status, "value") else str(appr.status)
    if status_str != ApprovalStatusEnum.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval request has already been processed (Current status: {status_str}).",
        )

    # Fetch Project
    proj_res = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    old_stage_val = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)
    target_enum = parse_stage_enum(appr.stage)

    # Update Approval Record
    appr.status = ApprovalStatusEnum.APPROVED
    appr.approved_by = current_user.name
    appr.approved_at = datetime.now(timezone.utc)
    if payload and payload.remarks:
        appr.remarks = payload.remarks

    # Update Project Stage
    if target_enum:
        project.current_stage = target_enum

    await evaluate_project_delays(session, project_id)

    # Notification
    notif = Notification(
        project_id=project_id,
        notification_type=NotificationTypeEnum.STAGE_CHANGE,
        title=f"Workflow Approved: {project.name}",
        message=f"Stage transition to '{appr.stage}' was approved by {current_user.name}.",
        is_read=False,
    )
    session.add(notif)

    # AuditLog
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="WORKFLOW",
        entity_id=appr.id,
        action="WORKFLOW_APPROVED",
        old_value={"stage": old_stage_val},
        new_value={"stage": appr.stage, "approved_by": current_user.name},
    )
    session.add(audit)
    await session.commit()
    await session.refresh(appr)

    return to_approval_response(appr)


@router.post("/projects/{project_id}/workflow/reject/{approval_id}", response_model=ApprovalResponse)
async def reject_workflow_request(
    project_id: str,
    approval_id: str,
    payload: ApprovalActionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.STATE_AUTHORITY,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """
    Rejects a pending workflow stage transition request. Remarks are REQUIRED.
    (Viewer role denied).
    """
    # Remarks Validation
    if not payload or not payload.remarks or not payload.remarks.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remarks are required when rejecting a workflow transition request.",
        )

    # Concurrency Lock / Select Approval
    appr_res = await session.execute(
        select(Approval).where(Approval.id == approval_id, Approval.project_id == project_id)
    )
    appr = appr_res.scalar_one_or_none()
    if not appr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")

    status_str = appr.status.value if hasattr(appr.status, "value") else str(appr.status)
    if status_str != ApprovalStatusEnum.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval request has already been processed (Current status: {status_str}).",
        )

    # Update Approval Record
    appr.status = ApprovalStatusEnum.REJECTED
    appr.approved_by = current_user.name
    appr.approved_at = datetime.now(timezone.utc)
    appr.remarks = payload.remarks.strip()

    # Project stage remains UNCHANGED

    # Notification
    notif = Notification(
        project_id=project_id,
        notification_type=NotificationTypeEnum.PROJECT_UPDATE,
        title=f"Workflow Request Rejected: {project_id}",
        message=f"Stage transition to '{appr.stage}' was rejected by {current_user.name}. Reason: {payload.remarks}",
        is_read=False,
    )
    session.add(notif)

    # AuditLog
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="WORKFLOW",
        entity_id=appr.id,
        action="WORKFLOW_REJECTED",
        old_value={"requested_stage": appr.stage},
        new_value={"remarks": payload.remarks, "rejected_by": current_user.name},
    )
    session.add(audit)
    await session.commit()
    await session.refresh(appr)

    return to_approval_response(appr)


@router.get("/projects/{project_id}/workflow/approvals", response_model=ApprovalListResponse)
async def list_project_approvals(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Lists all approval requests for a project."""
    stmt = select(Approval).where(Approval.project_id == project_id).order_by(Approval.created_at.desc())
    res = await session.execute(stmt)
    apprs = res.scalars().all()

    items = [to_approval_response(a) for a in apprs]
    return ApprovalListResponse(items=items, total=len(items))


@router.get("/projects/{project_id}/workflow/history", response_model=WorkflowHistoryResponse)
async def get_workflow_history(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieves chronological workflow history and current pending approval status."""
    proj_res = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    curr_stage_val = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)
    proj_status_val = project.status.value if hasattr(project.status, "value") else str(project.status)

    # Fetch Approvals
    appr_res = await session.execute(
        select(Approval).where(Approval.project_id == project_id).order_by(Approval.created_at.asc())
    )
    approvals = appr_res.scalars().all()

    # Find pending approval
    pending_appr = next((a for a in approvals if (a.status.value if hasattr(a.status, "value") else str(a.status)) == ApprovalStatusEnum.PENDING.value), None)

    history_items: List[WorkflowHistoryItem] = []
    for a in approvals:
        st_val = a.status.value if hasattr(a.status, "value") else str(a.status)
        action_name = f"WORKFLOW_{st_val}"
        user_name = a.approved_by if (st_val in ["APPROVED", "REJECTED"] and a.approved_by) else a.requested_by
        timestamp = a.approved_at or a.requested_at or a.created_at

        history_items.append(
            WorkflowHistoryItem(
                id=a.id,
                project_id=a.project_id,
                new_stage=a.stage,
                action=action_name,
                user=user_name,
                remarks=a.remarks,
                approval_status=st_val,
                timestamp=timestamp,
            )
        )

    return WorkflowHistoryResponse(
        project_id=project_id,
        current_stage=curr_stage_val,
        status=proj_status_val,
        history=history_items,
        pending_approval=to_approval_response(pending_appr) if pending_appr else None,
    )

