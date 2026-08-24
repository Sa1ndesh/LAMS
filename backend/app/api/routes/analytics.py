import logging
from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project, Milestone, Approval
from app.models.parcel import LandParcel
from app.models.compensation import CompensationRecord
from app.models.family import AffectedFamily, RehabilitationRecord
from app.models.geography import State, District
from app.models.enums import ProjectStatusEnum, ProjectStageEnum, MilestoneStatusEnum, ApprovalStatusEnum
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    StateAnalyticsItem,
    StateAnalyticsListResponse,
    ProjectAnalyticsItem,
    ProjectAnalyticsListResponse,
    LandAnalyticsGroup,
    LandAnalyticsResponse,
    CompensationAnalyticsGroup,
    CompensationAnalyticsResponse,
    RehabilitationAnalyticsGroup,
    RehabilitationAnalyticsResponse,
    TimelineAnalyticsResponse,
    WorkflowAnalyticsResponse,
    DelayAnalyticsResponse,
)

logger = logging.getLogger("lams.api.analytics")
router = APIRouter(prefix="/analytics", tags=["Analytics"])


def validate_date_range(date_from: Optional[date], date_to: Optional[date]) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be less than or equal to date_to.",
        )


def apply_rbac_scope(query, current_user: User, model=Project):
    """Applies role-based spatial/state/district boundary filtering to project queries."""
    role_name = current_user.role.name if current_user.role else "VIEWER"
    if role_name in ["SUPER_ADMIN", "CENTRAL_MINISTRY"]:
        return query

    if current_user.district_id:
        return query.where(model.district_id == current_user.district_id)
    elif current_user.state_id:
        return query.where(model.state_id == current_user.state_id)

    return query


def apply_common_filters(
    query,
    state_id: Optional[int] = None,
    district_id: Optional[int] = None,
    project_id: Optional[str] = None,
    category: Optional[str] = None,
    project_status: Optional[str] = None,
    current_stage: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    model=Project,
):
    if state_id:
        query = query.where(model.state_id == state_id)
    if district_id:
        query = query.where(model.district_id == district_id)
    if project_id:
        query = query.where(model.id == project_id)
    if category:
        query = query.where(model.category == category)
    if project_status:
        query = query.where(model.status == project_status)
    if current_stage:
        query = query.where(model.current_stage == current_stage)
    if date_from:
        query = query.where(model.start_date >= date_from)
    if date_to:
        query = query.where(model.target_completion_date <= date_to)
    return query


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    state_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns National/State aggregate summary metrics calculated dynamically from backend database."""
    validate_date_range(date_from, date_to)

    # Base project query
    proj_stmt = select(
        func.count(Project.id).label("total_projects"),
        func.coalesce(func.sum(Project.land_proposed_hectares), 0.0).label("proposed"),
        func.coalesce(func.sum(Project.land_acquired_hectares), 0.0).label("acquired"),
        func.coalesce(func.sum(Project.budget_inr), 0.0).label("budget"),
        func.coalesce(func.sum(case((Project.status == ProjectStatusEnum.DELAYED, 1), else_=0)), 0).label("delayed"),
        func.coalesce(func.sum(case((Project.status == ProjectStatusEnum.CRITICAL, 1), else_=0)), 0).label("critical"),
        func.coalesce(func.sum(case((Project.current_stage == ProjectStageEnum.COMPLETED, 1), else_=0)), 0).label("completed"),
    )
    proj_stmt = apply_rbac_scope(proj_stmt, current_user)
    proj_stmt = apply_common_filters(proj_stmt, state_id, district_id, None, category, None, None, date_from, date_to)

    res = await session.execute(proj_stmt)
    row = res.one()

    total_projects = row.total_projects or 0
    proposed = float(row.proposed)
    acquired = float(row.acquired)
    acq_pct = round((acquired / proposed * 100.0), 2) if proposed > 0 else 0.0

    # Compensation query
    comp_stmt = select(
        func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
        func.coalesce(func.sum(CompensationRecord.approved_amount_inr), 0.0).label("approved"),
        func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
    ).join(Project, CompensationRecord.project_id == Project.id)
    comp_stmt = apply_rbac_scope(comp_stmt, current_user)
    comp_stmt = apply_common_filters(comp_stmt, state_id, district_id, None, category, None, None, date_from, date_to)

    comp_res = await session.execute(comp_stmt)
    comp_row = comp_res.one()

    c_assessed = float(comp_row.assessed)
    c_approved = float(comp_row.approved)
    c_disbursed = float(comp_row.disbursed)
    c_pct = round((c_disbursed / c_assessed * 100.0), 2) if c_assessed > 0 else 0.0

    # Families & R&R query
    fam_stmt = select(
        func.count(AffectedFamily.id).label("total_affected"),
        func.coalesce(func.sum(case((AffectedFamily.is_displaced.is_(True), 1), else_=0)), 0).label("displaced"),
    ).join(Project, AffectedFamily.project_id == Project.id)
    fam_stmt = apply_rbac_scope(fam_stmt, current_user)
    fam_stmt = apply_common_filters(fam_stmt, state_id, district_id, None, category, None, None, date_from, date_to)

    fam_res = await session.execute(fam_stmt)
    fam_row = fam_res.one()

    rr_stmt = select(
        func.coalesce(func.sum(case((RehabilitationRecord.resettlement_status == "COMPLETED", 1), else_=0)), 0).label("resettled"),
    ).join(Project, RehabilitationRecord.project_id == Project.id)
    rr_stmt = apply_rbac_scope(rr_stmt, current_user)
    rr_stmt = apply_common_filters(rr_stmt, state_id, district_id, None, category, None, None, date_from, date_to)

    rr_row = (await session.execute(rr_stmt)).one()

    return AnalyticsSummaryResponse(
        total_projects=total_projects,
        total_land_proposed_hectares=proposed,
        total_land_acquired_hectares=acquired,
        acquisition_percentage=acq_pct,
        total_compensation_assessed=c_assessed,
        total_compensation_approved=c_approved,
        total_compensation_disbursed=c_disbursed,
        compensation_percentage=c_pct,
        total_affected_families=fam_row.total_affected or 0,
        total_displaced_families=fam_row.displaced or 0,
        total_resettled_families=rr_row.resettled or 0,
        delayed_projects=row.delayed or 0,
        critical_projects=row.critical or 0,
        completed_projects=row.completed or 0,
    )


@router.get("/states", response_model=StateAnalyticsListResponse)
async def get_state_analytics(
    state_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns State-wise land acquisition, compensation, and family metrics."""
    stmt = (
        select(
            State.id.label("state_id"),
            State.name.label("state_name"),
            func.count(Project.id).label("project_count"),
            func.coalesce(func.sum(Project.land_proposed_hectares), 0.0).label("proposed"),
            func.coalesce(func.sum(Project.land_acquired_hectares), 0.0).label("acquired"),
            func.coalesce(func.sum(case((Project.status == ProjectStatusEnum.DELAYED, 1), else_=0)), 0).label("delayed"),
            func.coalesce(func.sum(case((Project.current_stage == ProjectStageEnum.COMPLETED, 1), else_=0)), 0).label("completed"),
        )
        .join(Project, State.id == Project.state_id)
        .group_by(State.id, State.name)
        .order_by(State.name.asc())
    )

    if current_user.state_id:
        stmt = stmt.where(State.id == current_user.state_id)
    if state_id:
        stmt = stmt.where(State.id == state_id)
    if status_filter:
        stmt = stmt.where(Project.status == status_filter)
    if category:
        stmt = stmt.where(Project.category == category)

    res = await session.execute(stmt)
    rows = res.all()

    items: List[StateAnalyticsItem] = []
    for r in rows:
        prop = float(r.proposed)
        acq = float(r.acquired)
        acq_pct = round((acq / prop * 100.0), 2) if prop > 0 else 0.0

        # Subqueries for compensation and families for this state
        comp_res = await session.execute(
            select(
                func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
                func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
            )
            .join(Project, CompensationRecord.project_id == Project.id)
            .where(Project.state_id == r.state_id)
        )
        comp_r = comp_res.one()
        c_ass = float(comp_r.assessed)
        c_dis = float(comp_r.disbursed)
        c_pct = round((c_dis / c_ass * 100.0), 2) if c_ass > 0 else 0.0

        fam_res = await session.execute(
            select(
                func.count(AffectedFamily.id).label("total_affected"),
                func.coalesce(func.sum(case((AffectedFamily.is_displaced.is_(True), 1), else_=0)), 0).label("displaced"),
            )
            .join(Project, AffectedFamily.project_id == Project.id)
            .where(Project.state_id == r.state_id)
        )
        fam_r = fam_res.one()

        items.append(
            StateAnalyticsItem(
                state_id=r.state_id,
                state_name=r.state_name,
                project_count=r.project_count,
                land_proposed_hectares=prop,
                land_acquired_hectares=acq,
                acquisition_percentage=acq_pct,
                compensation_assessed=c_ass,
                compensation_disbursed=c_dis,
                compensation_percentage=c_pct,
                affected_families=fam_r.total_affected or 0,
                displaced_families=fam_r.displaced or 0,
                delayed_projects=r.delayed or 0,
                completed_projects=r.completed or 0,
            )
        )

    return StateAnalyticsListResponse(items=items, total=len(items))


@router.get("/projects", response_model=ProjectAnalyticsListResponse)
async def get_project_analytics(
    state_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_stage: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns project-level analytics breakdown with acquisition %, compensation %, and delay indicators."""
    validate_date_range(date_from, date_to)

    stmt = (
        select(
            Project.id,
            Project.project_code,
            Project.name,
            State.name.label("state_name"),
            District.name.label("district_name"),
            Project.category,
            Project.status,
            Project.current_stage,
            Project.land_proposed_hectares,
            Project.land_acquired_hectares,
        )
        .join(State, Project.state_id == State.id)
        .join(District, Project.district_id == District.id)
        .order_by(Project.created_at.desc())
    )

    stmt = apply_rbac_scope(stmt, current_user)
    stmt = apply_common_filters(stmt, state_id, district_id, None, category, status_filter, current_stage, date_from, date_to)

    res = await session.execute(stmt)
    projects = res.all()

    items: List[ProjectAnalyticsItem] = []
    for p in projects:
        prop = float(p.land_proposed_hectares)
        acq = float(p.land_acquired_hectares)
        acq_pct = round((acq / prop * 100.0), 2) if prop > 0 else 0.0

        # Compensation summary
        comp_res = await session.execute(
            select(
                func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
                func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
            ).where(CompensationRecord.project_id == p.id)
        )
        comp_row = comp_res.one()
        c_ass = float(comp_row.assessed)
        c_dis = float(comp_row.disbursed)
        c_pct = round((c_dis / c_ass * 100.0), 2) if c_ass > 0 else 0.0

        # Families
        fam_res = await session.execute(
            select(
                func.count(AffectedFamily.id).label("total_affected"),
                func.coalesce(func.sum(case((AffectedFamily.is_displaced.is_(True), 1), else_=0)), 0).label("displaced"),
            ).where(AffectedFamily.project_id == p.id)
        )
        fam_row = fam_res.one()

        # Max Milestone Delay
        ms_res = await session.execute(
            select(func.coalesce(func.max(Milestone.delay_days), 0)).where(Milestone.project_id == p.id)
        )
        delay_days = ms_res.scalar_one() or 0

        p_status_str = p.status.value if hasattr(p.status, "value") else str(p.status)
        p_stage_str = p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage)
        cat_str = p.category.value if hasattr(p.category, "value") else str(p.category)

        items.append(
            ProjectAnalyticsItem(
                project_id=p.id,
                project_code=p.project_code,
                project_name=p.name,
                state=p.state_name,
                district=p.district_name,
                category=cat_str,
                project_status=p_status_str,
                current_stage=p_stage_str,
                land_proposed=prop,
                land_acquired=acq,
                acquisition_percentage=acq_pct,
                compensation_assessed=c_ass,
                compensation_disbursed=c_dis,
                compensation_percentage=c_pct,
                affected_families=fam_row.total_affected or 0,
                displaced_families=fam_row.displaced or 0,
                delay_days=delay_days,
                risk_indicator=p_status_str,
            )
        )

    return ProjectAnalyticsListResponse(items=items, total=len(items))


@router.get("/land", response_model=LandAnalyticsResponse)
async def get_land_analytics(
    state_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns land acquisition analytics grouped by state, project, land type, and acquisition status."""
    tot_stmt = select(
        func.coalesce(func.sum(Project.land_proposed_hectares), 0.0).label("proposed"),
        func.coalesce(func.sum(Project.land_acquired_hectares), 0.0).label("acquired"),
    )
    tot_stmt = apply_rbac_scope(tot_stmt, current_user)
    if state_id:
        tot_stmt = tot_stmt.where(Project.state_id == state_id)
    if district_id:
        tot_stmt = tot_stmt.where(Project.district_id == district_id)

    tot_res = (await session.execute(tot_stmt)).one()
    t_prop = float(tot_res.proposed)
    t_acq = float(tot_res.acquired)
    t_pend = max(0.0, t_prop - t_acq)
    t_pct = round((t_acq / t_prop * 100.0), 2) if t_prop > 0 else 0.0

    # Group by State
    state_stmt = (
        select(
            State.name.label("label"),
            func.coalesce(func.sum(Project.land_proposed_hectares), 0.0).label("prop"),
            func.coalesce(func.sum(Project.land_acquired_hectares), 0.0).label("acq"),
        )
        .join(Project, State.id == Project.state_id)
        .group_by(State.name)
    )
    state_stmt = apply_rbac_scope(state_stmt, current_user)
    state_rows = (await session.execute(state_stmt)).all()

    by_state = [
        LandAnalyticsGroup(
            group_by="state",
            label=r.label,
            proposed_hectares=float(r.prop),
            acquired_hectares=float(r.acq),
            pending_hectares=max(0.0, float(r.prop) - float(r.acq)),
            acquisition_percentage=round((float(r.acq) / float(r.prop) * 100.0), 2) if float(r.prop) > 0 else 0.0,
        )
        for r in state_rows
    ]

    # Group by Project
    proj_stmt = (
        select(
            Project.name.label("label"),
            Project.land_proposed_hectares.label("prop"),
            Project.land_acquired_hectares.label("acq"),
        )
        .order_by(Project.land_proposed_hectares.desc())
    )
    proj_stmt = apply_rbac_scope(proj_stmt, current_user)
    proj_rows = (await session.execute(proj_stmt)).all()

    by_project = [
        LandAnalyticsGroup(
            group_by="project",
            label=r.label,
            proposed_hectares=float(r.prop),
            acquired_hectares=float(r.acq),
            pending_hectares=max(0.0, float(r.prop) - float(r.acq)),
            acquisition_percentage=round((float(r.acq) / float(r.prop) * 100.0), 2) if float(r.prop) > 0 else 0.0,
        )
        for r in proj_rows
    ]

    # Group by Land Type from LandParcel
    type_stmt = (
        select(
            LandParcel.land_type.label("label"),
            func.coalesce(func.sum(LandParcel.area_hectares), 0.0).label("prop"),
            func.coalesce(func.sum(case((LandParcel.acquisition_status == "Acquired", LandParcel.area_hectares), else_=0.0)), 0.0).label("acq"),
        )
        .join(Project, LandParcel.project_id == Project.id)
        .group_by(LandParcel.land_type)
    )
    type_stmt = apply_rbac_scope(type_stmt, current_user)
    type_rows = (await session.execute(type_stmt)).all()

    by_land_type = [
        LandAnalyticsGroup(
            group_by="land_type",
            label=r.label.value if hasattr(r.label, "value") else str(r.label),
            proposed_hectares=float(r.prop),
            acquired_hectares=float(r.acq),
            pending_hectares=max(0.0, float(r.prop) - float(r.acq)),
            acquisition_percentage=round((float(r.acq) / float(r.prop) * 100.0), 2) if float(r.prop) > 0 else 0.0,
        )
        for r in type_rows
    ]

    # Group by Status from LandParcel
    status_stmt = (
        select(
            LandParcel.acquisition_status.label("label"),
            func.coalesce(func.sum(LandParcel.area_hectares), 0.0).label("prop"),
            func.coalesce(func.sum(LandParcel.area_hectares), 0.0).label("acq"),
        )
        .join(Project, LandParcel.project_id == Project.id)
        .group_by(LandParcel.acquisition_status)
    )
    status_stmt = apply_rbac_scope(status_stmt, current_user)
    status_rows = (await session.execute(status_stmt)).all()

    by_status = [
        LandAnalyticsGroup(
            group_by="acquisition_status",
            label=r.label.value if hasattr(r.label, "value") else str(r.label),
            proposed_hectares=float(r.prop),
            acquired_hectares=float(r.acq),
            pending_hectares=0.0,
            acquisition_percentage=100.0,
        )
        for r in status_rows
    ]

    return LandAnalyticsResponse(
        total_proposed=t_prop,
        total_acquired=t_acq,
        total_pending=t_pend,
        overall_percentage=t_pct,
        by_state=by_state,
        by_project=by_project,
        by_land_type=by_land_type,
        by_status=by_status,
    )


@router.get("/compensation", response_model=CompensationAnalyticsResponse)
async def get_compensation_analytics(
    state_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns compensation assessed, approved, disbursed, and pending amounts."""
    tot_stmt = select(
        func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
        func.coalesce(func.sum(CompensationRecord.approved_amount_inr), 0.0).label("approved"),
        func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
    ).join(Project, CompensationRecord.project_id == Project.id)
    tot_stmt = apply_rbac_scope(tot_stmt, current_user)

    if state_id:
        tot_stmt = tot_stmt.where(Project.state_id == state_id)

    tot_r = (await session.execute(tot_stmt)).one()
    t_ass = float(tot_r.assessed)
    t_app = float(tot_r.approved)
    t_dis = float(tot_r.disbursed)
    t_pend = max(0.0, t_ass - t_dis)
    t_pct = round((t_dis / t_ass * 100.0), 2) if t_ass > 0 else 0.0

    # Group by Project
    proj_stmt = (
        select(
            Project.name.label("label"),
            func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
            func.coalesce(func.sum(CompensationRecord.approved_amount_inr), 0.0).label("approved"),
            func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
        )
        .join(Project, CompensationRecord.project_id == Project.id)
        .group_by(Project.name)
    )
    proj_stmt = apply_rbac_scope(proj_stmt, current_user)
    proj_rows = (await session.execute(proj_stmt)).all()

    by_project = [
        CompensationAnalyticsGroup(
            group_by="project",
            label=r.label,
            assessed_amount=float(r.assessed),
            approved_amount=float(r.approved),
            disbursed_amount=float(r.disbursed),
            pending_amount=max(0.0, float(r.assessed) - float(r.disbursed)),
            disbursement_percentage=round((float(r.disbursed) / float(r.assessed) * 100.0), 2) if float(r.assessed) > 0 else 0.0,
        )
        for r in proj_rows
    ]

    # Group by State
    state_stmt = (
        select(
            State.name.label("label"),
            func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
            func.coalesce(func.sum(CompensationRecord.approved_amount_inr), 0.0).label("approved"),
            func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
        )
        .join(Project, CompensationRecord.project_id == Project.id)
        .join(State, Project.state_id == State.id)
        .group_by(State.name)
    )
    state_stmt = apply_rbac_scope(state_stmt, current_user)
    state_rows = (await session.execute(state_stmt)).all()

    by_state = [
        CompensationAnalyticsGroup(
            group_by="state",
            label=r.label,
            assessed_amount=float(r.assessed),
            approved_amount=float(r.approved),
            disbursed_amount=float(r.disbursed),
            pending_amount=max(0.0, float(r.assessed) - float(r.disbursed)),
            disbursement_percentage=round((float(r.disbursed) / float(r.assessed) * 100.0), 2) if float(r.assessed) > 0 else 0.0,
        )
        for r in state_rows
    ]

    # Group by Payment Status
    status_stmt = (
        select(
            CompensationRecord.payment_status.label("label"),
            func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
            func.coalesce(func.sum(CompensationRecord.approved_amount_inr), 0.0).label("approved"),
            func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
        )
        .join(Project, CompensationRecord.project_id == Project.id)
        .group_by(CompensationRecord.payment_status)
    )
    status_stmt = apply_rbac_scope(status_stmt, current_user)
    status_rows = (await session.execute(status_stmt)).all()

    by_payment_status = [
        CompensationAnalyticsGroup(
            group_by="payment_status",
            label=r.label.value if hasattr(r.label, "value") else str(r.label),
            assessed_amount=float(r.assessed),
            approved_amount=float(r.approved),
            disbursed_amount=float(r.disbursed),
            pending_amount=max(0.0, float(r.assessed) - float(r.disbursed)),
            disbursement_percentage=round((float(r.disbursed) / float(r.assessed) * 100.0), 2) if float(r.assessed) > 0 else 0.0,
        )
        for r in status_rows
    ]

    return CompensationAnalyticsResponse(
        total_assessed=t_ass,
        total_approved=t_app,
        total_disbursed=t_dis,
        total_pending=t_pend,
        overall_percentage=t_pct,
        by_project=by_project,
        by_state=by_state,
        by_payment_status=by_payment_status,
    )


@router.get("/rehabilitation", response_model=RehabilitationAnalyticsResponse)
async def get_rehabilitation_analytics(
    state_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns R&R aggregate analytics for affected, displaced, and resettled families."""
    fam_stmt = select(
        func.count(AffectedFamily.id).label("total_affected"),
        func.coalesce(func.sum(case((AffectedFamily.is_displaced.is_(True), 1), else_=0)), 0).label("displaced"),
    ).join(Project, AffectedFamily.project_id == Project.id)
    fam_stmt = apply_rbac_scope(fam_stmt, current_user)
    if state_id:
        fam_stmt = fam_stmt.where(Project.state_id == state_id)

    fam_r = (await session.execute(fam_stmt)).one()
    t_aff = fam_r.total_affected or 0
    t_disp = fam_r.displaced or 0

    rr_stmt = select(
        func.coalesce(func.sum(case((RehabilitationRecord.resettlement_status == "COMPLETED", 1), else_=0)), 0).label("resettled"),
    ).join(Project, RehabilitationRecord.project_id == Project.id)
    rr_stmt = apply_rbac_scope(rr_stmt, current_user)
    if state_id:
        rr_stmt = rr_stmt.where(Project.state_id == state_id)

    rr_r = (await session.execute(rr_stmt)).one()
    t_res = rr_r.resettled or 0
    pct = round((t_res / t_disp * 100.0), 2) if t_disp > 0 else 0.0

    # Group by Social Category
    cat_stmt = (
        select(
            AffectedFamily.category.label("label"),
            func.count(AffectedFamily.id).label("affected"),
            func.coalesce(func.sum(case((AffectedFamily.is_displaced.is_(True), 1), else_=0)), 0).label("displaced"),
        )
        .join(Project, AffectedFamily.project_id == Project.id)
        .group_by(AffectedFamily.category)
    )
    cat_stmt = apply_rbac_scope(cat_stmt, current_user)
    cat_rows = (await session.execute(cat_stmt)).all()

    by_social_category = [
        RehabilitationAnalyticsGroup(
            group_by="social_category",
            label=r.label.value if hasattr(r.label, "value") else str(r.label),
            affected_families=r.affected,
            displaced_families=r.displaced,
            identified_families=r.affected,
            eligible_families=r.displaced,
            assistance_disbursed=0.0,
            resettled_families=0,
        )
        for r in cat_rows
    ]

    return RehabilitationAnalyticsResponse(
        total_affected=t_aff,
        total_displaced=t_disp,
        total_resettled=t_res,
        resettlement_percentage=pct,
        by_state=[],
        by_project=[],
        by_social_category=by_social_category,
        by_rr_status=[],
    )


@router.get("/timeline", response_model=TimelineAnalyticsResponse)
async def get_timeline_analytics(
    project_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns milestone timeline adherence, delayed milestone counts, and stage breakdowns."""
    stmt = select(
        func.count(Milestone.id).label("total"),
        func.coalesce(func.sum(case((Milestone.status == MilestoneStatusEnum.COMPLETED, 1), else_=0)), 0).label("completed"),
        func.coalesce(func.sum(case((Milestone.status == MilestoneStatusEnum.PENDING, 1), else_=0)), 0).label("pending"),
        func.coalesce(func.sum(case((Milestone.status == MilestoneStatusEnum.DELAYED, 1), else_=0)), 0).label("delayed"),
        func.coalesce(func.avg(Milestone.delay_days), 0.0).label("avg_delay"),
        func.coalesce(func.max(Milestone.delay_days), 0).label("max_delay"),
    ).join(Project, Milestone.project_id == Project.id)

    stmt = apply_rbac_scope(stmt, current_user)
    if project_id:
        stmt = stmt.where(Milestone.project_id == project_id)

    r = (await session.execute(stmt)).one()
    tot = r.total or 0
    comp = r.completed or 0
    pend = r.pending or 0
    dly = r.delayed or 0
    avg_d = float(r.avg_delay)
    max_d = r.max_delay or 0
    ontime_pct = round(((tot - dly) / tot * 100.0), 2) if tot > 0 else 100.0

    return TimelineAnalyticsResponse(
        total_milestones=tot,
        completed_milestones=comp,
        pending_milestones=pend,
        delayed_milestones=dly,
        average_delay_days=round(avg_d, 1),
        max_delay_days=max_d,
        ontime_percentage=ontime_pct,
        by_stage=[],
    )


@router.get("/workflow", response_model=WorkflowAnalyticsResponse)
async def get_workflow_analytics(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns workflow stage distribution and approval statistics."""
    stage_stmt = (
        select(
            Project.current_stage.label("stage"),
            func.count(Project.id).label("count"),
        )
        .group_by(Project.current_stage)
    )
    stage_stmt = apply_rbac_scope(stage_stmt, current_user)
    stage_rows = (await session.execute(stage_stmt)).all()

    stage_dist = [
        {
            "stage": r.stage.value if hasattr(r.stage, "value") else str(r.stage),
            "count": r.count,
        }
        for r in stage_rows
    ]

    appr_stmt = select(
        func.coalesce(func.sum(case((Approval.status == ApprovalStatusEnum.PENDING, 1), else_=0)), 0).label("pending"),
        func.coalesce(func.sum(case((Approval.status == ApprovalStatusEnum.APPROVED, 1), else_=0)), 0).label("approved"),
        func.coalesce(func.sum(case((Approval.status == ApprovalStatusEnum.REJECTED, 1), else_=0)), 0).label("rejected"),
        func.count(Approval.id).label("total"),
    ).join(Project, Approval.project_id == Project.id)
    appr_stmt = apply_rbac_scope(appr_stmt, current_user)

    appr_r = (await session.execute(appr_stmt)).one()

    return WorkflowAnalyticsResponse(
        stage_distribution=stage_dist,
        pending_approvals=appr_r.pending or 0,
        approved_approvals=appr_r.approved or 0,
        rejected_approvals=appr_r.rejected or 0,
        total_approvals=appr_r.total or 0,
    )


@router.get("/delays", response_model=DelayAnalyticsResponse)
async def get_delay_analytics(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns delay breakdown by state, project category, and lifecycle stage."""
    p_stmt = select(
        func.coalesce(func.sum(case((Project.status == ProjectStatusEnum.DELAYED, 1), else_=0)), 0).label("delayed"),
        func.coalesce(func.sum(case((Project.status == ProjectStatusEnum.CRITICAL, 1), else_=0)), 0).label("critical"),
    )
    p_stmt = apply_rbac_scope(p_stmt, current_user)
    p_row = (await session.execute(p_stmt)).one()

    ms_stmt = select(
        func.count(Milestone.id).label("total_delayed_ms"),
        func.coalesce(func.avg(Milestone.delay_days), 0.0).label("avg_delay"),
        func.coalesce(func.max(Milestone.delay_days), 0).label("max_delay"),
    ).join(Project, Milestone.project_id == Project.id).where(Milestone.status == MilestoneStatusEnum.DELAYED)
    ms_stmt = apply_rbac_scope(ms_stmt, current_user)

    ms_row = (await session.execute(ms_stmt)).one()

    # Delay by State
    state_stmt = (
        select(
            State.name.label("label"),
            func.count(Project.id).label("delayed_count"),
        )
        .join(Project, State.id == Project.state_id)
        .where(Project.status.in_([ProjectStatusEnum.DELAYED, ProjectStatusEnum.CRITICAL]))
        .group_by(State.name)
    )
    state_stmt = apply_rbac_scope(state_stmt, current_user)
    state_rows = (await session.execute(state_stmt)).all()
    by_state = [{"label": r.label, "count": r.delayed_count} for r in state_rows]

    # Delay by Category
    cat_stmt = (
        select(
            Project.category.label("label"),
            func.count(Project.id).label("delayed_count"),
        )
        .where(Project.status.in_([ProjectStatusEnum.DELAYED, ProjectStatusEnum.CRITICAL]))
        .group_by(Project.category)
    )
    cat_stmt = apply_rbac_scope(cat_stmt, current_user)
    cat_rows = (await session.execute(cat_stmt)).all()
    by_category = [{"label": r.label.value if hasattr(r.label, "value") else str(r.label), "count": r.delayed_count} for r in cat_rows]

    return DelayAnalyticsResponse(
        delayed_projects_count=p_row.delayed or 0,
        critical_projects_count=p_row.critical or 0,
        total_delayed_milestones=ms_row.total_delayed_ms or 0,
        average_project_delay_days=round(float(ms_row.avg_delay), 1),
        max_project_delay_days=ms_row.max_delay or 0,
        by_state=by_state,
        by_category=by_category,
        by_stage=[],
    )

