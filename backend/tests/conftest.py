import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal, engine
from app.models.user import User
from app.core.security import create_access_token


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    """Dispose engine connections after each test to prevent event loop mismatch with asyncpg."""
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_admin_user():
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User).where(User.email == "admin.national@lams.gov.in").options(selectinload(User.role))
        )
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def seeded_viewer_user():
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User).where(User.email == "survey.field@lams.gov.in").options(selectinload(User.role))
        )
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def admin_token(seeded_admin_user):
    if seeded_admin_user:
        return create_access_token(subject=seeded_admin_user.id, role="SUPER_ADMIN")
    return create_access_token(subject="admin-test-uuid", role="SUPER_ADMIN")


@pytest_asyncio.fixture
async def viewer_token(seeded_viewer_user):
    if seeded_viewer_user:
        return create_access_token(subject=seeded_viewer_user.id, role="FIELD_OFFICER")
    return create_access_token(subject="viewer-test-uuid", role="FIELD_OFFICER")


@pytest_asyncio.fixture
async def admin_token_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def viewer_token_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
