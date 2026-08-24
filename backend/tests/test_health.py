import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root GET / endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "National Land Acquisition" in data["service"]
        assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test health GET /api/health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "LAMS Backend" in data["service"]
        assert data["version"] == "1.0.0"

