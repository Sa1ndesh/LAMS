import logging
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.compensation import CompensationRecord
from app.models.parcel import LandParcel
from app.models.enums import UserRoleEnum, PaymentStatusEnum
from app.schemas.compensation import CompensationCreate, CompensationUpdate, CompensationResponse, CompensationListResponse

logger = logging.getLogger("lams.api.compensation")
router = APIRouter(tags=["Compensation"])


@router.get("/projects/{project_id}/compensation", response_model=CompensationListResponse)
async def list_project_compensation(
    project_id: str,
    status_filter: Optional[PaymentStatusEnum] = Query(None, alias="payment_status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List compensation records for a project."""
    stmt = (
        select(CompensationRecord)
        .where(CompensationRecord.project_id == project_id)
        .options(selectinload(CompensationRecord.parcel).selectinload(LandParcel.owners))
    )

    if status_filter:
        stmt = stmt.where(CompensationRecord.payment_status == status_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    offset = (page - 1) * page_size
    stmt = stmt.order_by(CompensationRecord.created_at.desc()).offset(offset).limit(page_size)
    res = await session.execute(stmt)
    records = res.scalars().all()

    items = []
    for r in records:
        survey_number = r.parcel.survey_number if r.parcel else None
        owner_name = r.parcel.owners[0].display_name if r.parcel and r.parcel.owners else None
        items.append(
            CompensationResponse(
                id=r.id,
                project_id=r.project_id,
                parcel_id=r.parcel_id,
                survey_number=survey_number,
                owner_name=owner_name,
                assessed_amount_inr=r.assessed_amount_inr,
                approved_amount_inr=r.approved_amount_inr,
                disbursed_amount_inr=r.disbursed_amount_inr,
                pending_amount_inr=r.pending_amount_inr,
                payment_status=r.payment_status.value if hasattr(r.payment_status, "value") else str(r.payment_status),
                payment_date=r.payment_date,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )

    total_pages = ceil(total / page_size) if total > 0 else 1
    return CompensationListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post("/projects/{project_id}/compensation", response_model=CompensationResponse, status_code=status.HTTP_201_CREATED)
async def create_compensation(
    project_id: str,
    payload: CompensationCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """Register new land parcel compensation assessment."""
    if payload.disbursed_amount_inr > payload.approved_amount_inr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disbursed amount cannot exceed approved amount.",
        )

    rec = CompensationRecord(
        project_id=project_id,
        parcel_id=payload.parcel_id,
        assessed_amount_inr=payload.assessed_amount_inr,
        approved_amount_inr=payload.approved_amount_inr,
        disbursed_amount_inr=payload.disbursed_amount_inr,
        payment_status=payload.payment_status,
        payment_date=payload.payment_date,
    )
    session.add(rec)
    await session.commit()
    await session.refresh(rec)

    return CompensationResponse(
        id=rec.id,
        project_id=rec.project_id,
        parcel_id=rec.parcel_id,
        assessed_amount_inr=rec.assessed_amount_inr,
        approved_amount_inr=rec.approved_amount_inr,
        disbursed_amount_inr=rec.disbursed_amount_inr,
        pending_amount_inr=rec.pending_amount_inr,
        payment_status=rec.payment_status.value if hasattr(rec.payment_status, "value") else str(rec.payment_status),
        payment_date=rec.payment_date,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )


@router.put("/compensation/{id}", response_model=CompensationResponse)
async def update_compensation(
    id: str,
    payload: CompensationUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.DISTRICT_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
        )
    ),
):
    """Update compensation disbursement status & amounts."""
    res = await session.execute(select(CompensationRecord).where(CompensationRecord.id == id))
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compensation record not found.")

    new_approved = payload.approved_amount_inr if payload.approved_amount_inr is not None else rec.approved_amount_inr
    new_disbursed = payload.disbursed_amount_inr if payload.disbursed_amount_inr is not None else rec.disbursed_amount_inr

    if new_disbursed > new_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disbursed amount cannot exceed approved amount.",
        )

    if payload.assessed_amount_inr is not None:
        rec.assessed_amount_inr = payload.assessed_amount_inr
    rec.approved_amount_inr = new_approved
    rec.disbursed_amount_inr = new_disbursed

    if payload.payment_status is not None:
        rec.payment_status = payload.payment_status
    if payload.payment_date is not None:
        rec.payment_date = payload.payment_date

    await session.commit()
    await session.refresh(rec)

    return CompensationResponse(
        id=rec.id,
        project_id=rec.project_id,
        parcel_id=rec.parcel_id,
        assessed_amount_inr=rec.assessed_amount_inr,
        approved_amount_inr=rec.approved_amount_inr,
        disbursed_amount_inr=rec.disbursed_amount_inr,
        pending_amount_inr=rec.pending_amount_inr,
        payment_status=rec.payment_status.value if hasattr(rec.payment_status, "value") else str(rec.payment_status),
        payment_date=rec.payment_date,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )

