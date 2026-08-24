import logging
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.project import Project
from app.models.parcel import LandParcel, LandOwner
from app.models.enums import UserRoleEnum, LandTypeEnum, ParcelAcquisitionStatusEnum
from app.schemas.parcel import ParcelCreate, ParcelUpdate, ParcelResponse, ParcelListResponse

logger = logging.getLogger("lams.api.parcels")
router = APIRouter(tags=["Land Parcels"])


async def recalculate_project_acquired_land(project_id: str, session: AsyncSession):
    """Calculates total acquired land area for a project and updates project record."""
    stmt = (
        select(func.sum(LandParcel.area_hectares))
        .where(
            LandParcel.project_id == project_id,
            LandParcel.acquisition_status == ParcelAcquisitionStatusEnum.ACQUIRED,
        )
    )
    res = await session.execute(stmt)
    total_acquired = res.scalar() or 0.0

    proj_res = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_res.scalar_one_or_none()
    if project:
        project.land_acquired_hectares = round(float(total_acquired), 2)
        await session.flush()


@router.get("/projects/{project_id}/parcels", response_model=ParcelListResponse)
async def list_project_parcels(
    project_id: str,
    search: Optional[str] = Query(None, description="Search survey number, owner name or village"),
    land_type: Optional[LandTypeEnum] = Query(None),
    status_filter: Optional[ParcelAcquisitionStatusEnum] = Query(None, alias="acquisition_status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List land parcels for a project with search & filter support."""
    stmt = (
        select(LandParcel)
        .where(LandParcel.project_id == project_id)
        .options(selectinload(LandParcel.owners))
    )

    if search:
        q = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                LandParcel.survey_number.ilike(q),
                LandParcel.parcel_code.ilike(q),
                LandParcel.village.ilike(q),
                LandParcel.taluk.ilike(q),
            )
        )

    if land_type:
        stmt = stmt.where(LandParcel.land_type == land_type)
    if status_filter:
        stmt = stmt.where(LandParcel.acquisition_status == status_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    offset = (page - 1) * page_size
    stmt = stmt.order_by(LandParcel.created_at.desc()).offset(offset).limit(page_size)
    res = await session.execute(stmt)
    parcels = res.scalars().all()

    items = []
    for p in parcels:
        owner_name = p.owners[0].display_name if p.owners else None
        items.append(
            ParcelResponse(
                id=p.id,
                project_id=p.project_id,
                parcel_code=p.parcel_code,
                survey_number=p.survey_number,
                state_id=p.state_id,
                district_id=p.district_id,
                taluk=p.taluk,
                village=p.village,
                area_hectares=p.area_hectares,
                land_type=p.land_type.value if hasattr(p.land_type, "value") else str(p.land_type),
                acquisition_status=p.acquisition_status.value if hasattr(p.acquisition_status, "value") else str(p.acquisition_status),
                compensation_status=p.compensation_status.value if hasattr(p.compensation_status, "value") else str(p.compensation_status),
                possession_status=p.possession_status.value if hasattr(p.possession_status, "value") else str(p.possession_status),
                latitude=p.latitude,
                longitude=p.longitude,
                owner_name=owner_name,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    total_pages = ceil(total / page_size) if total > 0 else 1
    return ParcelListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post("/projects/{project_id}/parcels", response_model=ParcelResponse, status_code=status.HTTP_201_CREATED)
async def create_parcel(
    project_id: str,
    payload: ParcelCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
            UserRoleEnum.FIELD_OFFICER,
        )
    ),
):
    """Add new land parcel to project."""
    # Check survey number unique within project
    check_stmt = select(LandParcel).where(
        LandParcel.project_id == project_id,
        LandParcel.survey_number == payload.survey_number,
    )
    if (await session.execute(check_stmt)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Survey number '{payload.survey_number}' already exists in this project.",
        )

    # Generate parcel code
    clean_survey = payload.survey_number.replace("/", "-").replace(" ", "")
    parcel_code = f"PCL-{clean_survey}"

    parcel = LandParcel(
        project_id=project_id,
        parcel_code=parcel_code,
        survey_number=payload.survey_number,
        state_id=payload.state_id,
        district_id=payload.district_id,
        taluk=payload.taluk,
        village=payload.village,
        area_hectares=payload.area_hectares,
        land_type=payload.land_type,
        acquisition_status=payload.acquisition_status,
        compensation_status=payload.compensation_status,
        possession_status=payload.possession_status,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    session.add(parcel)
    await session.flush()

    if payload.owner_name:
        owner = LandOwner(
            parcel_id=parcel.id,
            owner_reference=f"REF-{payload.survey_number}",
            display_name=payload.owner_name,
        )
        session.add(owner)

    await recalculate_project_acquired_land(project_id, session)
    await session.commit()
    await session.refresh(parcel)

    return ParcelResponse(
        id=parcel.id,
        project_id=parcel.project_id,
        parcel_code=parcel.parcel_code,
        survey_number=parcel.survey_number,
        state_id=parcel.state_id,
        district_id=parcel.district_id,
        taluk=parcel.taluk,
        village=parcel.village,
        area_hectares=parcel.area_hectares,
        land_type=parcel.land_type.value if hasattr(parcel.land_type, "value") else str(parcel.land_type),
        acquisition_status=parcel.acquisition_status.value if hasattr(parcel.acquisition_status, "value") else str(parcel.acquisition_status),
        compensation_status=parcel.compensation_status.value if hasattr(parcel.compensation_status, "value") else str(parcel.compensation_status),
        possession_status=parcel.possession_status.value if hasattr(parcel.possession_status, "value") else str(parcel.possession_status),
        latitude=parcel.latitude,
        longitude=parcel.longitude,
        owner_name=payload.owner_name,
        created_at=parcel.created_at,
        updated_at=parcel.updated_at,
    )


@router.put("/parcels/{parcel_id}", response_model=ParcelResponse)
async def update_parcel(
    parcel_id: str,
    payload: ParcelUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
            UserRoleEnum.FIELD_OFFICER,
        )
    ),
):
    """Update parcel status & acquisition stage."""
    stmt = select(LandParcel).where(LandParcel.id == parcel_id).options(selectinload(LandParcel.owners))
    res = await session.execute(stmt)
    parcel = res.scalar_one_or_none()

    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Land parcel not found.")

    if payload.area_hectares is not None:
        parcel.area_hectares = payload.area_hectares
    if payload.land_type is not None:
        parcel.land_type = payload.land_type
    if payload.acquisition_status is not None:
        parcel.acquisition_status = payload.acquisition_status
    if payload.compensation_status is not None:
        parcel.compensation_status = payload.compensation_status
    if payload.possession_status is not None:
        parcel.possession_status = payload.possession_status
    if payload.latitude is not None:
        parcel.latitude = payload.latitude
    if payload.longitude is not None:
        parcel.longitude = payload.longitude

    if payload.owner_name is not None and parcel.owners:
        parcel.owners[0].display_name = payload.owner_name

    await recalculate_project_acquired_land(parcel.project_id, session)
    await session.commit()
    await session.refresh(parcel)

    owner_name = parcel.owners[0].display_name if parcel.owners else None
    return ParcelResponse(
        id=parcel.id,
        project_id=parcel.project_id,
        parcel_code=parcel.parcel_code,
        survey_number=parcel.survey_number,
        state_id=parcel.state_id,
        district_id=parcel.district_id,
        taluk=parcel.taluk,
        village=parcel.village,
        area_hectares=parcel.area_hectares,
        land_type=parcel.land_type.value if hasattr(parcel.land_type, "value") else str(parcel.land_type),
        acquisition_status=parcel.acquisition_status.value if hasattr(parcel.acquisition_status, "value") else str(parcel.acquisition_status),
        compensation_status=parcel.compensation_status.value if hasattr(parcel.compensation_status, "value") else str(parcel.compensation_status),
        possession_status=parcel.possession_status.value if hasattr(parcel.possession_status, "value") else str(parcel.possession_status),
        latitude=parcel.latitude,
        longitude=parcel.longitude,
        owner_name=owner_name,
        created_at=parcel.created_at,
        updated_at=parcel.updated_at,
    )


@router.delete("/parcels/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parcel(
    parcel_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """Delete land parcel."""
    res = await session.execute(select(LandParcel).where(LandParcel.id == parcel_id))
    parcel = res.scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Land parcel not found.")

    project_id = parcel.project_id
    await session.delete(parcel)
    await recalculate_project_acquired_land(project_id, session)
    await session.commit()
    return None

