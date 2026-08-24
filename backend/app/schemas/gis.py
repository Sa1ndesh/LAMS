from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class GeoJSONPolygonGeometry(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]] = Field(
        ...,
        description="List of coordinate rings where each coordinate is [longitude, latitude]",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_rings(cls, v: List[List[List[float]]]) -> List[List[List[float]]]:
        if not v or len(v) == 0:
            raise ValueError("Polygon geometry must contain at least one exterior linear ring.")
        
        exterior = v[0]
        if len(exterior) < 4:
            raise ValueError("Polygon exterior ring must contain at least 4 coordinate pairs.")

        # Check closed ring
        if exterior[0] != exterior[-1]:
            # Auto-close ring if identical first/last missing
            exterior.append(exterior[0])

        for pt in exterior:
            if len(pt) < 2:
                raise ValueError("Each coordinate point must have [longitude, latitude].")
            lon, lat = pt[0], pt[1]
            if not (-180.0 <= lon <= 180.0):
                raise ValueError(f"Longitude {lon} out of valid range [-180, 180].")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude {lat} out of valid range [-90, 90].")

        return v


class GeoJSONFeatureProperties(BaseModel):
    parcel_id: str
    parcel_code: str
    survey_number: str
    area_hectares: float
    land_type: str
    acquisition_status: str
    compensation_status: str
    possession_status: str
    village: str
    taluk: str


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONPolygonGeometry
    properties: GeoJSONFeatureProperties


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature]


class ProjectGISSummary(BaseModel):
    project_id: str
    project_name: str
    project_code: str
    parcel_count: int
    acquired_area_hectares: float
    bounding_box: List[float] = Field(
        default_factory=lambda: [77.5, 12.9, 77.8, 13.1],
        description="Bounding box coordinates [min_lon, min_lat, max_lon, max_lat]",
    )
    geojson: GeoJSONFeatureCollection


class SaveParcelGeometryPayload(BaseModel):
    survey_number: str = Field(..., example="104/A")
    coordinates: List[List[float]] = Field(
        ...,
        description="Array of [longitude, latitude] coordinate pairs forming a polygon",
    )
    area_hectares: Optional[float] = Field(default=None, ge=0.0)

