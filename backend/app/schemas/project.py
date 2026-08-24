from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ProjectCategoryEnum, ProjectStageEnum, ProjectStatusEnum


class ProjectCreate(BaseModel):
    project_code: str = Field(..., min_length=3, max_length=50, json_schema_extra={"example": "LAMS-KA-2026-010"})
    name: str = Field(..., min_length=3, max_length=255, json_schema_extra={"example": "Peripheral Ring Road Phase II"})
    category: ProjectCategoryEnum = Field(..., json_schema_extra={"example": ProjectCategoryEnum.HIGHWAY})
    ministry: str = Field(..., json_schema_extra={"example": "Ministry of Road Transport and Highways"})
    implementing_agency: str = Field(..., json_schema_extra={"example": "Bangalore Development Authority"})
    state_id: int = Field(..., json_schema_extra={"example": 1})
    district_id: int = Field(..., json_schema_extra={"example": 1})
    village: str = Field(..., json_schema_extra={"example": "Hebbal & Yelahanka"})
    land_proposed_hectares: float = Field(..., ge=0.0, json_schema_extra={"example": 350.0})
    land_acquired_hectares: float = Field(default=0.0, ge=0.0, json_schema_extra={"example": 0.0})
    budget_inr: float = Field(..., ge=0.0, json_schema_extra={"example": 15000000000.0})
    current_stage: ProjectStageEnum = Field(default=ProjectStageEnum.PROPOSAL)
    status: ProjectStatusEnum = Field(default=ProjectStatusEnum.ACTIVE)
    start_date: date = Field(..., json_schema_extra={"example": "2026-04-01"})
    target_completion_date: date = Field(..., json_schema_extra={"example": "2028-03-31"})
    description: Optional[str] = Field(default=None, max_length=1000)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=255)
    category: Optional[ProjectCategoryEnum] = None
    ministry: Optional[str] = None
    implementing_agency: Optional[str] = None
    village: Optional[str] = None
    land_proposed_hectares: Optional[float] = Field(default=None, ge=0.0)
    land_acquired_hectares: Optional[float] = Field(default=None, ge=0.0)
    budget_inr: Optional[float] = Field(default=None, ge=0.0)
    current_stage: Optional[ProjectStageEnum] = None
    status: Optional[ProjectStatusEnum] = None
    target_completion_date: Optional[date] = None
    description: Optional[str] = None


class StateSummary(BaseModel):
    id: int
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True)


class DistrictSummary(BaseModel):
    id: int
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    id: str
    project_code: str
    name: str
    category: str
    ministry: str
    implementing_agency: str
    state_id: int
    district_id: int
    state_name: Optional[str] = None
    district_name: Optional[str] = None
    village: str
    land_proposed_hectares: float
    land_acquired_hectares: float
    budget_inr: float
    current_stage: str
    status: str
    start_date: date
    target_completion_date: date
    description: Optional[str] = None
    acquisition_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

