import logging
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.project import Project
from app.models.parcel import LandParcel
from app.models.enums import UserRoleEnum
from app.schemas.gis import (
    GeoJSONFeatureCollection,
    GeoJSONFeature,
    GeoJSONPolygonGeometry,
    GeoJSONFeatureProperties,
    ProjectGISSummary,
    SaveParcelGeometryPayload,
)

logger = logging.getLogger("lams.api.gis")
router = APIRouter(prefix="/gis", tags=["GIS & GeoJSON"])


def build_default_polygon(lat: float, lng: float, delta: float = 0.003) -> List[List[List[float]]]:
    """Generates standard rectangular polygon ring around central lat/lng if no custom boundary set."""
    if lat == 0.0 or lng == 0.0:
        lng, lat = 77.5946, 12.9716

    return [[
        [round(lng - delta, 6), round(lat - delta, 6)],
        [round(lng + delta, 6), round(lat - delta, 6)],
        [round(lng + delta, 6), round(lat + delta, 6)],
        [round(lng - delta, 6), round(lat + delta, 6)],
        [round(lng - delta, 6), round(lat - delta, 6)],
    ]]


def parse_geometry_coordinates(raw_geom, lat: float, lng: float) -> List[List[List[float]]]:
    """Extracts polygon coordinates array from PostGIS GeoJSON string, dict, or fallback."""
    if not raw_geom:
        return build_default_polygon(lat, lng)

    try:
        if isinstance(raw_geom, str):
            parsed = json.loads(raw_geom)
            if "coordinates" in parsed:
                return parsed["coordinates"]
        elif isinstance(raw_geom, dict):
            if "coordinates" in raw_geom:
                return raw_geom["coordinates"]
    except Exception as e:
        logger.warning(f"Error parsing geometry: {e}")

    return build_default_polygon(lat, lng)


def compute_bounding_box(features: List[GeoJSONFeature]) -> List[float]:
    """Computes bounding box [min_lon, min_lat, max_lon, max_lat] from feature geometries."""
    if not features:
        return [77.5, 12.9, 77.8, 13.1]

    min_lon, min_lat = 180.0, 90.0
    max_lon, max_lat = -180.0, -90.0

    for f in features:
        for pt in f.geometry.coordinates[0]:
            lon, lat = pt[0], pt[1]
            if lon < min_lon: min_lon = lon
            if lon > max_lon: max_lon = lon
            if lat < min_lat: min_lat = lat
            if lat > max_lat: max_lat = lat

    return [round(min_lon, 6), round(min_lat, 6), round(max_lon, 6), round(max_lat, 6)]


@router.get("/projects/{project_id}", response_model=ProjectGISSummary)
async def get_project_gis_summary(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve project-level GIS summary, bounding box & GeoJSON FeatureCollection."""
    proj_res = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    # Query parcel fields and PostGIS ST_AsGeoJSON(geometry)
    stmt = select(
        LandParcel,
        func.ST_AsGeoJSON(LandParcel.geometry).label("postgis_geojson"),
    ).where(LandParcel.project_id == project_id)

    res = await session.execute(stmt)
    rows = res.all()

    features: List[GeoJSONFeature] = []
    for p, postgis_geojson in rows:
        raw_geom = postgis_geojson or p.geometry
        coords = parse_geometry_coordinates(raw_geom, p.latitude, p.longitude)
        
        feature = GeoJSONFeature(
            geometry=GeoJSONPolygonGeometry(type="Polygon", coordinates=coords),
            properties=GeoJSONFeatureProperties(
                parcel_id=p.id,
                parcel_code=p.parcel_code,
                survey_number=p.survey_number,
                area_hectares=p.area_hectares,
                land_type=p.land_type.value if hasattr(p.land_type, "value") else str(p.land_type),
                acquisition_status=p.acquisition_status.value if hasattr(p.acquisition_status, "value") else str(p.acquisition_status),
                compensation_status=p.compensation_status.value if hasattr(p.compensation_status, "value") else str(p.compensation_status),
                possession_status=p.possession_status.value if hasattr(p.possession_status, "value") else str(p.possession_status),
                village=p.village,
                taluk=p.taluk,
            ),
        )
        features.append(feature)

    feature_collection = GeoJSONFeatureCollection(features=features)
    bbox = compute_bounding_box(features)

    return ProjectGISSummary(
        project_id=project.id,
        project_name=project.name,
        project_code=project.project_code,
        parcel_count=len(rows),
        acquired_area_hectares=project.land_acquired_hectares,
        bounding_box=bbox,
        geojson=feature_collection,
    )


@router.get("/projects/{project_id}/parcels", response_model=GeoJSONFeatureCollection)
async def get_project_parcels_geojson(
    project_id: str,
    min_lon: Optional[float] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve GeoJSON FeatureCollection for project parcels with bounding box filtering."""
    stmt = select(
        LandParcel,
        func.ST_AsGeoJSON(LandParcel.geometry).label("postgis_geojson"),
    ).where(LandParcel.project_id == project_id)

    # Optional Bounding Box Filter
    if min_lon is not None and max_lon is not None:
        stmt = stmt.where(LandParcel.longitude >= min_lon, LandParcel.longitude <= max_lon)
    if min_lat is not None and max_lat is not None:
        stmt = stmt.where(LandParcel.latitude >= min_lat, LandParcel.latitude <= max_lat)

    rows = (await session.execute(stmt)).all()

    features: List[GeoJSONFeature] = []
    for p, postgis_geojson in rows:
        raw_geom = postgis_geojson or p.geometry
        coords = parse_geometry_coordinates(raw_geom, p.latitude, p.longitude)
        
        feature = GeoJSONFeature(
            geometry=GeoJSONPolygonGeometry(type="Polygon", coordinates=coords),
            properties=GeoJSONFeatureProperties(
                parcel_id=p.id,
                parcel_code=p.parcel_code,
                survey_number=p.survey_number,
                area_hectares=p.area_hectares,
                land_type=p.land_type.value if hasattr(p.land_type, "value") else str(p.land_type),
                acquisition_status=p.acquisition_status.value if hasattr(p.acquisition_status, "value") else str(p.acquisition_status),
                compensation_status=p.compensation_status.value if hasattr(p.compensation_status, "value") else str(p.compensation_status),
                possession_status=p.possession_status.value if hasattr(p.possession_status, "value") else str(p.possession_status),
                village=p.village,
                taluk=p.taluk,
            ),
        )
        features.append(feature)

    return GeoJSONFeatureCollection(features=features)


@router.post("/projects/{project_id}/parcels/geometry", status_code=status.HTTP_200_OK)
async def update_parcel_geometry(
    project_id: str,
    payload: SaveParcelGeometryPayload,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(
        require_roles(
            UserRoleEnum.SUPER_ADMIN,
            UserRoleEnum.LAND_ACQUISITION_OFFICER,
            UserRoleEnum.FIELD_OFFICER,
        )
    ),
):
    """Save or update parcel boundary geometry polygon."""
    stmt = select(LandParcel).where(
        LandParcel.project_id == project_id,
        LandParcel.survey_number == payload.survey_number,
    )
    parcel = (await session.execute(stmt)).scalar_one_or_none()

    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with survey number '{payload.survey_number}' not found in this project.",
        )

    # Validate ring
    coords = payload.coordinates
    if len(coords) < 4:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Polygon must contain at least 4 points.")

    if coords[0] != coords[-1]:
        coords.append(coords[0])

    # Convert coordinates ring to WKT string
    wkt_pts = ", ".join([f"{pt[0]} {pt[1]}" for pt in coords])
    wkt = f"POLYGON(({wkt_pts}))"

    await session.execute(
        text("UPDATE land_parcels SET geometry = ST_GeomFromText(:wkt, 4326) WHERE id = :id"),
        {"wkt": wkt, "id": parcel.id},
    )

    if payload.area_hectares is not None:
        parcel.area_hectares = payload.area_hectares

    await session.commit()
    return {"message": f"Geometry updated for parcel survey #{payload.survey_number}."}
