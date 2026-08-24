import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.geography import State
from app.schemas.ai import (
    ProjectRiskResponse,
    ProjectInsightResponse,
    AIOverviewResponse,
    HighRiskProjectItem,
)
from app.services.ai_decision_support import (
    get_project_risk_analysis,
    get_project_insights_analysis,
    generate_ai_overview,
)

logger = logging.getLogger("lams.api.ai")
router = APIRouter(prefix="/ai", tags=["AI Decision Support"])


def check_project_rbac_scope(project: Project, current_user: User) -> None:
    role_name = current_user.role.name if current_user.role else "VIEWER"
    if role_name in ["SUPER_ADMIN", "CENTRAL_MINISTRY"]:
        return

    if current_user.district_id and project.district_id != current_user.district_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Access restricted to assigned district scope.",
        )
    elif current_user.state_id and project.state_id != current_user.state_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Access restricted to assigned state scope.",
        )


@router.get("/projects/{project_id}/risk", response_model=ProjectRiskResponse)
async def get_project_risk(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns complete explainable decision-support risk analysis for a project."""
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    check_project_rbac_scope(project, current_user)
    return await get_project_risk_analysis(session, project)


@router.get("/projects/{project_id}/insights", response_model=ProjectInsightResponse)
async def get_project_insights(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns detailed operational bottlenecks and recommended actions for a project."""
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    check_project_rbac_scope(project, current_user)
    return await get_project_insights_analysis(session, project)


@router.get("/overview", response_model=AIOverviewResponse)
async def get_ai_overview(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns national AI decision-support executive overview."""
    stmt = select(Project).options(selectinload(Project.state))

    role_name = current_user.role.name if current_user.role else "VIEWER"
    if role_name not in ["SUPER_ADMIN", "CENTRAL_MINISTRY"]:
        if current_user.district_id:
            stmt = stmt.where(Project.district_id == current_user.district_id)
        elif current_user.state_id:
            stmt = stmt.where(Project.state_id == current_user.state_id)

    res = await session.execute(stmt)
    projects = res.scalars().all()

    return await generate_ai_overview(session, list(projects))


@router.get("/projects/high-risk", response_model=List[HighRiskProjectItem])
async def get_high_risk_projects(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns projects ordered by risk score descending."""
    overview = await get_ai_overview(session, current_user)
    return overview.highest_risk_projects

