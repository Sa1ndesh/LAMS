import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, Role
from app.models.enums import UserRoleEnum
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse

logger = logging.getLogger("lams.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegister,
    session: AsyncSession = Depends(get_async_session),
):
    """User registration endpoint. Arbitrary public creation of SUPER_ADMIN is restricted."""
    if payload.role == UserRoleEnum.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot register SUPER_ADMIN via public registration.",
        )

    # Check for duplicate email
    res = await session.execute(select(User).where(User.email == payload.email))
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered.",
        )

    # Find target role
    role_res = await session.execute(select(Role).where(Role.name == payload.role.value))
    role_obj = role_res.scalar_one_or_none()
    if not role_obj:
        # Fallback to VIEWER
        v_res = await session.execute(select(Role).where(Role.name == "VIEWER"))
        role_obj = v_res.scalar_one_or_none()
        if not role_obj:
            role_obj = Role(name="VIEWER", description="Read Only Viewer")
            session.add(role_obj)
            await session.flush()

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role_obj.id,
        state_id=payload.state_id,
        district_id=payload.district_id,
        is_active=True,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=role_obj.name,
        state_id=new_user.state_id,
        district_id=new_user.district_id,
        is_active=new_user.is_active,
    )


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    session: AsyncSession = Depends(get_async_session),
):
    """User login endpoint returning JWT bearer token."""
    stmt = select(User).where(User.email == payload.email).options(selectinload(User.role))
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    # Generic authentication error to avoid user enumeration
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name = user.role.name if user.role else "VIEWER"
    access_token = create_access_token(
        subject=user.id,
        role=role_name,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns currently authenticated user profile information."""
    role_name = current_user.role.name if current_user.role else "VIEWER"
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=role_name,
        state_id=current_user.state_id,
        district_id=current_user.district_id,
        is_active=current_user.is_active,
    )


@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    """Test endpoint requiring active authentication."""
    role_name = current_user.role.name if current_user.role else "VIEWER"
    return {
        "message": "Authenticated access granted",
        "user_id": current_user.id,
        "email": current_user.email,
        "role": role_name,
    }


@router.get("/admin-test")
async def admin_only_endpoint(
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
):
    """Test endpoint requiring SUPER_ADMIN authorization."""
    return {
        "message": "Admin authorization granted",
        "user_id": current_user.id,
        "role": "SUPER_ADMIN",
    }

