import logging
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles, check_project_access_scope
from app.models.user import User
from app.models.project import Project
from app.models.geography import State, District
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.models.enums import UserRoleEnum, ProjectCategoryEnum, ProjectStageEnum, ProjectStatusEnum, NotificationTypeEnum
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse

logger = logging.getLogger("lams.api.projects")
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    search: Optional[str] = Query(None, description="Search by name, code, district or village"),
    state_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    category: Optional[ProjectCategoryEnum] = Query(None),
    status_filter: Optional[ProjectStatusEnum] = Query(None, alias="status"),
    stage_filter: Optional[ProjectStageEnum] = Query(None, alias="current_stage"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List projects with search, filter, and pagination support."""
    stmt = select(Project).options(selectinload(Project.state), selectinload(Project.district))

    # Apply Search Filter
    if search:
        q = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Project.name.ilike(q),
                Project.project_code.ilike(q),
                Project.village.ilike(q),
                Project.implementing_agency.ilike(q),
            )
        )

    # Apply Field Filters
    if state_id:
        stmt = stmt.where(Project.state_id == state_id)
    if district_id:
        stmt = stmt.where(Project.district_id == district_id)
    if category:
        stmt = stmt.where(Project.category == category)
    if status_filter:
        stmt = stmt.where(Project.status == status_filter)
    if stage_filter:
        stmt = stmt.where(Project.current_stage == stage_filter)

    # Count Total Matches
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Apply Pagination & Ordering
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Project.created_at.desc()).offset(offset).limit(page_size)
    res = await session.execute(stmt)
    projects = res.scalars().all()

    items = []
    for p in projects:
        pct = round((p.land_acquired_hectares / p.land_proposed_hectares * 100), 1) if p.land_proposed_hectares > 0 else 0.0
        items.append(
            ProjectResponse(
                id=p.id,
                project_code=p.project_code,
                name=p.name,
                category=p.category.value if hasattr(p.category, "value") else str(p.category),
                ministry=p.ministry,
                implementing_agency=p.implementing_agency,
                state_id=p.state_id,
                district_id=p.district_id,
                state_name=p.state.name if p.state else None,
                district_name=p.district.name if p.district else None,
                village=p.village,
                land_proposed_hectares=p.land_proposed_hectares,
                land_acquired_hectares=p.land_acquired_hectares,
                budget_inr=p.budget_inr,
                current_stage=p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage),
                status=p.status.value if hasattr(p.status, "value") else str(p.status),
                start_date=p.start_date,
                target_completion_date=p.target_completion_date,
                description=p.description,
                acquisition_percentage=pct,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    total_pages = ceil(total / page_size) if total > 0 else 1
    return ProjectListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed project information."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.state), selectinload(Project.district))
    )
    res = await session.execute(stmt)
    p = res.scalar_one_or_none()

    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    check_project_access_scope(p, current_user)

    pct = round((p.land_acquired_hectares / p.land_proposed_hectares * 100), 1) if p.land_proposed_hectares > 0 else 0.0
    return ProjectResponse(
        id=p.id,
        project_code=p.project_code,
        name=p.name,
        category=p.category.value if hasattr(p.category, "value") else str(p.category),
        ministry=p.ministry,
        implementing_agency=p.implementing_agency,
        state_id=p.state_id,
        district_id=p.district_id,
        state_name=p.state.name if p.state else None,
        district_name=p.district.name if p.district else None,
        village=p.village,
        land_proposed_hectares=p.land_proposed_hectares,
        land_acquired_hectares=p.land_acquired_hectares,
        budget_inr=p.budget_inr,
        current_stage=p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage),
        status=p.status.value if hasattr(p.status, "value") else str(p.status),
        start_date=p.start_date,
        target_completion_date=p.target_completion_date,
        description=p.description,
        acquisition_percentage=pct,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.STATE_AUTHORITY,
        )
    ),
):
    """Propose new project with RBAC authorization."""
    # Check duplicate code
    res = await session.execute(select(Project).where(Project.project_code == payload.project_code))
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project code '{payload.project_code}' already exists.",
        )

    p = Project(
        project_code=payload.project_code,
        name=payload.name,
        category=payload.category,
        ministry=payload.ministry,
        implementing_agency=payload.implementing_agency,
        state_id=payload.state_id,
        district_id=payload.district_id,
        village=payload.village,
        land_proposed_hectares=payload.land_proposed_hectares,
        land_acquired_hectares=payload.land_acquired_hectares,
        budget_inr=payload.budget_inr,
        current_stage=payload.current_stage,
        status=payload.status,
        start_date=payload.start_date,
        target_completion_date=payload.target_completion_date,
        description=payload.description,
    )
    session.add(p)
    await session.flush()

    # Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="Project",
        entity_id=p.id,
        action="CREATE",
        new_value={"project_code": p.project_code, "name": p.name},
    )
    session.add(audit)

    await session.commit()
    await session.refresh(p)

    # Reload relationships
    stmt = (
        select(Project)
        .where(Project.id == p.id)
        .options(selectinload(Project.state), selectinload(Project.district))
    )
    r_p = (await session.execute(stmt)).scalar_one()

    return ProjectResponse(
        id=r_p.id,
        project_code=r_p.project_code,
        name=r_p.name,
        category=r_p.category.value if hasattr(r_p.category, "value") else str(r_p.category),
        ministry=r_p.ministry,
        implementing_agency=r_p.implementing_agency,
        state_id=r_p.state_id,
        district_id=r_p.district_id,
        state_name=r_p.state.name if r_p.state else None,
        district_name=r_p.district.name if r_p.district else None,
        village=r_p.village,
        land_proposed_hectares=r_p.land_proposed_hectares,
        land_acquired_hectares=r_p.land_acquired_hectares,
        budget_inr=r_p.budget_inr,
        current_stage=r_p.current_stage.value if hasattr(r_p.current_stage, "value") else str(r_p.current_stage),
        status=r_p.status.value if hasattr(r_p.status, "value") else str(r_p.status),
        start_date=r_p.start_date,
        target_completion_date=r_p.target_completion_date,
        description=r_p.description,
        acquisition_percentage=0.0,
        created_at=r_p.created_at,
        updated_at=r_p.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
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
    """Update project details & lifecycle stage."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.state), selectinload(Project.district))
    )
    res = await session.execute(stmt)
    p = res.scalar_one_or_none()

    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    old_stage = p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage)

    # Apply updates
    if payload.name is not None:
        p.name = payload.name
    if payload.category is not None:
        p.category = payload.category
    if payload.ministry is not None:
        p.ministry = payload.ministry
    if payload.implementing_agency is not None:
        p.implementing_agency = payload.implementing_agency
    if payload.village is not None:
        p.village = payload.village
    if payload.land_proposed_hectares is not None:
        p.land_proposed_hectares = payload.land_proposed_hectares
    if payload.land_acquired_hectares is not None:
        p.land_acquired_hectares = payload.land_acquired_hectares
    if payload.budget_inr is not None:
        p.budget_inr = payload.budget_inr
    if payload.current_stage is not None:
        p.current_stage = payload.current_stage
    if payload.status is not None:
        p.status = payload.status
    if payload.target_completion_date is not None:
        p.target_completion_date = payload.target_completion_date
    if payload.description is not None:
        p.description = payload.description

    new_stage = p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage)

    # If stage changed, log notification
    if old_stage != new_stage:
        notif = Notification(
            project_id=p.id,
            notification_type=NotificationTypeEnum.STAGE_CHANGE,
            title=f"Stage Advanced to {new_stage}",
            message=f"Project stage updated from {old_stage} to {new_stage}.",
            is_read=False,
        )
        session.add(notif)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        entity_type="Project",
        entity_id=p.id,
        action="UPDATE",
        new_value={"stage": new_stage, "status": str(p.status)},
    )
    session.add(audit)

    await session.commit()
    await session.refresh(p)

    pct = round((p.land_acquired_hectares / p.land_proposed_hectares * 100), 1) if p.land_proposed_hectares > 0 else 0.0
    return ProjectResponse(
        id=p.id,
        project_code=p.project_code,
        name=p.name,
        category=p.category.value if hasattr(p.category, "value") else str(p.category),
        ministry=p.ministry,
        implementing_agency=p.implementing_agency,
        state_id=p.state_id,
        district_id=p.district_id,
        state_name=p.state.name if p.state else None,
        district_name=p.district.name if p.district else None,
        village=p.village,
        land_proposed_hectares=p.land_proposed_hectares,
        land_acquired_hectares=p.land_acquired_hectares,
        budget_inr=p.budget_inr,
        current_stage=p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage),
        status=p.status.value if hasattr(p.status, "value") else str(p.status),
        start_date=p.start_date,
        target_completion_date=p.target_completion_date,
        description=p.description,
        acquisition_percentage=pct,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
):
    """Delete project with SUPER_ADMIN authorization."""
    res = await session.execute(select(Project).where(Project.id == project_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    await session.delete(p)
    await session.commit()
    return None

