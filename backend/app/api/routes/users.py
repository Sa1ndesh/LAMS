import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.enums import UserRoleEnum
from app.schemas.auth import UserResponse

logger = logging.getLogger("lams.api.users")
router = APIRouter(tags=["Users Management"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.DISTRICT_ADMIN,
        )
    ),
):
    """List system users."""
    stmt = select(User).options(selectinload(User.role)).order_by(User.created_at.desc())
    res = await session.execute(stmt)
    users = res.scalars().all()

    return [
        UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role.name if u.role else "VIEWER",
            state_id=u.state_id,
            district_id=u.district_id,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.CENTRAL_MINISTRY,
            UserRoleEnum.DISTRICT_ADMIN,
        )
    ),
):
    """Get single user profile."""
    stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.name if user.role else "VIEWER",
        state_id=user.state_id,
        district_id=user.district_id,
        is_active=user.is_active,
    )


@router.put("/users/{user_id}/status", response_model=UserResponse)
async def toggle_user_status(
    user_id: str,
    is_active: bool,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
):
    """Enable or disable user account (SUPER_ADMIN only)."""
    stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_active = is_active
    await session.commit()
    await session.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.name if user.role else "VIEWER",
        state_id=user.state_id,
        district_id=user.district_id,
        is_active=user.is_active,
    )

