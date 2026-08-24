from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_async_session

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns backend operational status.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=f"{settings.APP_SHORT_NAME} Backend",
        version=settings.VERSION,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Readiness Check",
    description="Verifies database connectivity.",
)
async def readiness_check(session: AsyncSession = Depends(get_async_session)) -> ReadinessResponse:
    try:
        res = await session.execute(text("SELECT 1"))
        res.scalar_one()
        return ReadinessResponse(
            status="ok",
            database="connected",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failure",
        )
