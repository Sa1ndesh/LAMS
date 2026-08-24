import logging
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.family import AffectedFamily
from app.models.enums import UserRoleEnum, SocialCategoryEnum, RRStatusEnum
from app.schemas.family import FamilyCreate, FamilyUpdate, FamilyResponse, FamilyListResponse

logger = logging.getLogger("lams.api.families")
router = APIRouter(tags=["Affected Families"])


@router.get("/projects/{project_id}/families", response_model=FamilyListResponse)
async def list_project_families(
    project_id: str,
    search: Optional[str] = Query(None, description="Search by family ref ID or village"),
    category: Optional[SocialCategoryEnum] = Query(None),
    rr_status: Optional[RRStatusEnum] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List affected family records for a project."""
    stmt = select(AffectedFamily).where(AffectedFamily.project_id == project_id)

    if search:
        q = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                AffectedFamily.family_reference_id.ilike(q),
                AffectedFamily.village.ilike(q),
            )
        )

    if category:
        stmt = stmt.where(AffectedFamily.category == category)
    if rr_status:
        stmt = stmt.where(AffectedFamily.rr_status == rr_status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = stmt.order_by(AffectedFamily.created_at.desc()).offset(offset).limit(page_size)
    families = (await session.execute(stmt)).scalars().all()

    items = [
        FamilyResponse(
            id=f.id,
            project_id=f.project_id,
            family_reference_id=f.family_reference_id,
            head_of_family=f.family_reference_id.replace("FAM-", "Head "),
            village=f.village,
            family_members_count=4,
            category=f.category.value if hasattr(f.category, "value") else str(f.category),
            is_affected=f.is_affected,
            is_displaced=f.is_displaced,
            rr_status=f.rr_status.value if hasattr(f.rr_status, "value") else str(f.rr_status),
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
        for f in families
    ]

    total_pages = ceil(total / page_size) if total > 0 else 1
    return FamilyListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post("/projects/{project_id}/families", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    project_id: str,
    payload: FamilyCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """Register affected family record."""
    ref_id = payload.family_reference_id or f"FAM-KA-2026-{(await session.execute(select(func.count(AffectedFamily.id)))).scalar_one() + 101}"

    fam = AffectedFamily(
        project_id=project_id,
        family_reference_id=ref_id,
        village=payload.village,
        category=payload.category,
        is_affected=payload.is_affected,
        is_displaced=payload.is_displaced,
        rr_status=payload.rr_status,
    )
    session.add(fam)
    await session.commit()
    await session.refresh(fam)

    return FamilyResponse(
        id=fam.id,
        project_id=fam.project_id,
        family_reference_id=fam.family_reference_id,
        head_of_family=payload.head_of_family,
        village=fam.village,
        family_members_count=payload.family_members_count,
        category=fam.category.value if hasattr(fam.category, "value") else str(fam.category),
        is_affected=fam.is_affected,
        is_displaced=fam.is_displaced,
        rr_status=fam.rr_status.value if hasattr(fam.rr_status, "value") else str(fam.rr_status),
        created_at=fam.created_at,
        updated_at=fam.updated_at,
    )


@router.put("/families/{id}", response_model=FamilyResponse)
async def update_family(
    id: str,
    payload: FamilyUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """Update family R&R record."""
    res = await session.execute(select(AffectedFamily).where(AffectedFamily.id == id))
    fam = res.scalar_one_or_none()
    if not fam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family record not found.")

    if payload.village is not None:
        fam.village = payload.village
    if payload.category is not None:
        fam.category = payload.category
    if payload.is_displaced is not None:
        fam.is_displaced = payload.is_displaced
    if payload.rr_status is not None:
        fam.rr_status = payload.rr_status

    await session.commit()
    await session.refresh(fam)

    head_name = payload.head_of_family or fam.family_reference_id.replace("FAM-", "Head ")
    return FamilyResponse(
        id=fam.id,
        project_id=fam.project_id,
        family_reference_id=fam.family_reference_id,
        head_of_family=head_name,
        village=fam.village,
        family_members_count=payload.family_members_count or 4,
        category=fam.category.value if hasattr(fam.category, "value") else str(fam.category),
        is_affected=fam.is_affected,
        is_displaced=fam.is_displaced,
        rr_status=fam.rr_status.value if hasattr(fam.rr_status, "value") else str(fam.rr_status),
        created_at=fam.created_at,
        updated_at=fam.updated_at,
    )


@router.delete("/families/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.DISTRICT_ADMIN,
        )
    ),
):
    """Delete family record."""
    res = await session.execute(select(AffectedFamily).where(AffectedFamily.id == id))
    fam = res.scalar_one_or_none()
    if not fam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family record not found.")

    await session.delete(fam)
    await session.commit()
    return None

