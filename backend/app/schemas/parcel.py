from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import LandTypeEnum, ParcelAcquisitionStatusEnum, CompensationStatusEnum, PossessionStatusEnum


class ParcelCreate(BaseModel):
    survey_number: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "104/A"})
    state_id: int = Field(..., json_schema_extra={"example": 1})
    district_id: int = Field(..., json_schema_extra={"example": 1})
    taluk: str = Field(..., json_schema_extra={"example": "KR Puram"})
    village: str = Field(..., json_schema_extra={"example": "Whitefield"})
    area_hectares: float = Field(..., ge=0.0, json_schema_extra={"example": 2.45})
    land_type: LandTypeEnum = Field(default=LandTypeEnum.AGRICULTURAL)
    acquisition_status: ParcelAcquisitionStatusEnum = Field(default=ParcelAcquisitionStatusEnum.PROPOSED)
    compensation_status: CompensationStatusEnum = Field(default=CompensationStatusEnum.PENDING)
    possession_status: PossessionStatusEnum = Field(default=PossessionStatusEnum.NOT_TAKEN)
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0, json_schema_extra={"example": 12.9698})
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0, json_schema_extra={"example": 77.7499})
    owner_name: Optional[str] = Field(default=None, json_schema_extra={"example": "Venkatesh Gowda"})


class ParcelUpdate(BaseModel):
    area_hectares: Optional[float] = Field(default=None, ge=0.0)
    land_type: Optional[LandTypeEnum] = None
    acquisition_status: Optional[ParcelAcquisitionStatusEnum] = None
    compensation_status: Optional[CompensationStatusEnum] = None
    possession_status: Optional[PossessionStatusEnum] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    owner_name: Optional[str] = None


class ParcelResponse(BaseModel):
    id: str
    project_id: str
    parcel_code: str
    survey_number: str
    state_id: int
    district_id: int
    taluk: str
    village: str
    area_hectares: float
    land_type: str
    acquisition_status: str
    compensation_status: str
    possession_status: str
    latitude: float
    longitude: float
    owner_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParcelListResponse(BaseModel):
    items: List[ParcelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

