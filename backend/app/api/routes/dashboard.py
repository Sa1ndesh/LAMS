import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.geography import State
from app.models.compensation import CompensationRecord
from app.models.family import AffectedFamily
from app.models.enums import ProjectStatusEnum
from app.schemas.dashboard import DashboardSummary, StateProgressItem, StageDistributionItem

logger = logging.getLogger("lams.api.dashboard")
router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Calculates executive dashboard summary metrics dynamically from database."""
    # 1. Total Projects
    total_projects = (await session.execute(select(func.count(Project.id)))).scalar_one() or 0

    # 2. Land Proposed & Acquired
    proposed_sum = (await session.execute(select(func.sum(Project.land_proposed_hectares)))).scalar() or 0.0
    acquired_sum = (await session.execute(select(func.sum(Project.land_acquired_hectares)))).scalar() or 0.0
    acq_pct = round((acquired_sum / proposed_sum * 100), 1) if proposed_sum > 0 else 0.0

    # 3. Compensation Assessed, Approved, Disbursed
    assessed_sum = (await session.execute(select(func.sum(CompensationRecord.assessed_amount_inr)))).scalar() or 0.0
    disbursed_sum = (await session.execute(select(func.sum(CompensationRecord.disbursed_amount_inr)))).scalar() or 0.0
    approved_sum = (await session.execute(select(func.sum(CompensationRecord.approved_amount_inr)))).scalar() or 0.0
    pending_sum = max(0.0, approved_sum - disbursed_sum)

    # 4. Affected & Displaced Families
    fam_count = (await session.execute(select(func.count(AffectedFamily.id)))).scalar_one() or 0
    displaced_count = (await session.execute(
        select(func.count(AffectedFamily.id)).where(AffectedFamily.is_displaced.is_(True))
    )).scalar_one() or 0

    # 5. Delayed Projects
    delayed_count = (await session.execute(
        select(func.count(Project.id)).where(
            or_(
                Project.status == ProjectStatusEnum.DELAYED,
                Project.status == ProjectStatusEnum.CRITICAL,
            )
        )
    )).scalar_one() or 0

    # 6. State Progress Aggregation
    state_stmt = (
        select(
            State.name,
            func.sum(Project.land_proposed_hectares).label("proposed"),
            func.sum(Project.land_acquired_hectares).label("acquired"),
        )
        .join(Project, Project.state_id == State.id)
        .group_by(State.name)
    )
    state_rows = (await session.execute(state_stmt)).all()
    state_progress = [
        StateProgressItem(
            state=row[0],
            target=round(row[1] or 0.0, 2),
            acquired=round(row[2] or 0.0, 2),
            percentage=round(((row[2] or 0.0) / (row[1] or 1.0) * 100), 1) if (row[1] or 0.0) > 0 else 0.0,
        )
        for row in state_rows
    ]

    # 7. Stage Distribution
    stage_stmt = select(Project.current_stage, func.count(Project.id)).group_by(Project.current_stage)
    stage_rows = (await session.execute(stage_stmt)).all()
    stage_distribution = [
        StageDistributionItem(
            stage=row[0].value if hasattr(row[0], "value") else str(row[0]),
            count=row[1],
        )
        for row in stage_rows
    ]

    return DashboardSummary(
        total_projects=total_projects,
        land_proposed_hectares=round(proposed_sum, 2),
        land_acquired_hectares=round(acquired_sum, 2),
        acquisition_percentage=acq_pct,
        compensation_assessed_inr=assessed_sum,
        compensation_disbursed_inr=disbursed_sum,
        compensation_pending_inr=pending_sum,
        affected_families_count=fam_count,
        displaced_families_count=displaced_count,
        delayed_projects_count=delayed_count,
        state_progress=state_progress,
        stage_distribution=stage_distribution,
    )

