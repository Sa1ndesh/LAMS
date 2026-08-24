import logging
from typing import List, Callable, Optional
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.database import get_async_session
from app.core.security import decode_access_token
from app.models.user import User, Role
from app.models.project import Project
from app.models.enums import UserRoleEnum

logger = logging.getLogger("lams.dependencies")
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    token_query: Optional[str] = Query(None, alias="token"),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Extracts Bearer JWT token from header or query param, decodes payload, and returns active User."""
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif token_query:
        token = token_query

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: Subject missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from Database with role eagerly loaded
    try:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"Database query failed in get_current_user: {e}")
        user = None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or credentials revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: UserRoleEnum) -> Callable:
    """RBAC Dependency generator enforcing that current user role matches one of allowed_roles."""
    allowed_role_names = {r.value for r in allowed_roles}

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_name = current_user.role.name if current_user.role else "VIEWER"
        if user_role_name not in allowed_role_names:
            logger.warning(f"Access denied for user {current_user.email} (Role: {user_role_name}). Allowed: {allowed_role_names}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of the following roles: {', '.join(allowed_role_names)}.",
            )
        return current_user

    return role_checker


def check_project_access_scope(project: Project, current_user: User) -> None:
    """Enforces spatial state/district boundary isolation on specific project resource access (IDOR / BOLA protection)."""
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
