import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.parcel import LandParcel
from app.core.security import create_access_token


@pytest_asyncio.fixture
async def seeded_admin_user():
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User).where(User.email == "admin.national@lams.gov.in").options(selectinload(User.role))
        )
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def sample_project():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Project).limit(1))
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def sample_parcel(sample_project):
    if not sample_project:
        return None
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(LandParcel).where(LandParcel.project_id == sample_project.id).limit(1)
        )
        return res.scalar_one_or_none()


@pytest_asyncio.fixture
async def admin_token(seeded_admin_user):
    if seeded_admin_user:
        return create_access_token(subject=seeded_admin_user.id, role="SUPER_ADMIN")
    return create_access_token(subject="admin-test-uuid", role="SUPER_ADMIN")


@pytest.mark.asyncio
async def test_get_project_gis_summary(admin_token, sample_project):
    """Test GET /api/gis/projects/{project_id}."""
    if not sample_project:
        pytest.skip("No sample project in database")

    headers = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/gis/projects/{sample_project.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "bounding_box" in data
        assert "geojson" in data
        assert data["geojson"]["type"] == "FeatureCollection"
        assert len(data["geojson"]["features"]) >= 1


@pytest.mark.asyncio
async def test_get_project_parcels_geojson_with_bbox(admin_token, sample_project):
    """Test GET /api/gis/projects/{project_id}/parcels with bounding box params."""
    if not sample_project:
        pytest.skip("No sample project in database")

    headers = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Query bounding box matching project region
        response = await client.get(
            f"/api/gis/projects/{sample_project.id}/parcels?min_lon=70.0&max_lon=85.0&min_lat=8.0&max_lat=30.0",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) >= 1

        # Check Polygon feature geometry structure
        feat = data["features"][0]
        assert feat["geometry"]["type"] == "Polygon"
        ring = feat["geometry"]["coordinates"][0]
        assert len(ring) >= 4
        # Validate closed ring (first coordinate == last coordinate)
        assert ring[0] == ring[-1]
        # Validate coordinate order [lon, lat]
        lon, lat = ring[0][0], ring[0][1]
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0


@pytest.mark.asyncio
async def test_update_parcel_geometry(admin_token, sample_project, sample_parcel):
    """Test POST /api/gis/projects/{project_id}/parcels/geometry."""
    if not sample_project or not sample_parcel:
        pytest.skip("No sample project or parcel in database")

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "survey_number": sample_parcel.survey_number,
        "coordinates": [
            [77.5900, 12.9700],
            [77.5940, 12.9700],
            [77.5940, 12.9740],
            [77.5900, 12.9740],
            [77.5900, 12.9700],
        ],
        "area_hectares": 3.5,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/gis/projects/{sample_project.id}/parcels/geometry",
            headers=headers,
            json=payload,
        )
        assert response.status_code == 200
        res_json = response.json()
        assert "message" in res_json
