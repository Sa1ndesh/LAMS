import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Milestone
from app.schemas.milestone import MilestoneCreate, MilestoneUpdate, MilestoneResponse, MilestoneListResponse

logger = logging.getLogger("lams.api.milestones")
router = APIRouter(tags=["Milestones"])


def calculate_delay(planned_date: date, actual_date: Optional[date]) -> Optional[int]:
    """Calculates milestone delay in days."""
    if not actual_date:
        today = date.today()
        if today > planned_date:
            return (today - planned_date).days
        return 0
    if actual_date > planned_date:
        return (actual_date - planned_date).days
    return 0


@router.get("/projects/{project_id}/milestones", response_model=MilestoneListResponse)
async def list_project_milestones(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List milestones for a project."""
    stmt = select(Milestone).where(Milestone.project_id == project_id).order_by(Milestone.planned_date.asc())
    res = await session.execute(stmt)
    milestones = res.scalars().all()

    items = []
    for m in milestones:
        delay = calculate_delay(m.planned_date, m.actual_date)
        items.append(
            MilestoneResponse(
                id=m.id,
                project_id=m.project_id,
                title=m.title,
                stage=m.stage,
                planned_date=m.planned_date,
                actual_date=m.actual_date,
                status=m.status.value if hasattr(m.status, "value") else str(m.status),
                delay_days=delay,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
        )

    return MilestoneListResponse(items=items, total=len(items))


@router.post("/projects/{project_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    project_id: str,
    payload: MilestoneCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Create milestone entry."""
    delay = calculate_delay(payload.planned_date, payload.actual_date)
    m = Milestone(
        project_id=project_id,
        title=payload.title,
        stage=payload.stage,
        planned_date=payload.planned_date,
        actual_date=payload.actual_date,
        status=payload.status,
        delay_days=delay,
    )
    session.add(m)
    await session.commit()
    await session.refresh(m)

    return MilestoneResponse(
        id=m.id,
        project_id=m.project_id,
        title=m.title,
        stage=m.stage,
        planned_date=m.planned_date,
        actual_date=m.actual_date,
        status=m.status.value if hasattr(m.status, "value") else str(m.status),
        delay_days=delay,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


@router.put("/milestones/{id}", response_model=MilestoneResponse)
async def update_milestone(
    id: str,
    payload: MilestoneUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Update milestone completion date & status."""
    res = await session.execute(select(Milestone).where(Milestone.id == id))
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found.")

    if payload.actual_date is not None:
        m.actual_date = payload.actual_date
    if payload.status is not None:
        m.status = payload.status

    m.delay_days = calculate_delay(m.planned_date, m.actual_date)

    await session.commit()
    await session.refresh(m)

    return MilestoneResponse(
        id=m.id,
        project_id=m.project_id,
        title=m.title,
        stage=m.stage,
        planned_date=m.planned_date,
        actual_date=m.actual_date,
        status=m.status.value if hasattr(m.status, "value") else str(m.status),
        delay_days=m.delay_days,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )

