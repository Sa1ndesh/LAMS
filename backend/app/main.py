import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.parcels import router as parcels_router
from app.api.routes.compensation import router as compensation_router
from app.api.routes.families import router as families_router
from app.api.routes.documents import router as documents_router
from app.api.routes.milestones import router as milestones_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.users import router as users_router
from app.api.routes.gis import router as gis_router
from app.api.routes.workflow import router as workflow_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.ai import router as ai_router

# Configure Application Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("lams.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} [{settings.APP_ENV}]...")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


# Create FastAPI Application Instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Centralized digital platform for monitoring national land acquisition lifecycles.",
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Configure CORS Middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register API Routers under /api
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(projects_router, prefix=settings.API_PREFIX)
app.include_router(parcels_router, prefix=settings.API_PREFIX)
app.include_router(compensation_router, prefix=settings.API_PREFIX)
app.include_router(families_router, prefix=settings.API_PREFIX)
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(milestones_router, prefix=settings.API_PREFIX)
app.include_router(notifications_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(gis_router, prefix=settings.API_PREFIX)
app.include_router(workflow_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(ai_router, prefix=settings.API_PREFIX)


# Root Endpoint
@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Root API Endpoint",
    description="Returns backend portal status and documentation links.",
)
async def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
        "auth": f"{settings.API_PREFIX}/auth/login",
    }


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Consistent error handler for validation failures."""
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error occurred.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Global exception handler avoiding stack trace exposure in production."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred.",
        },
    )
