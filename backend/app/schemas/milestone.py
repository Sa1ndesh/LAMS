from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import MilestoneStatusEnum


class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, json_schema_extra={"example": "Section 11 Gazette Notification"})
    stage: str = Field(..., json_schema_extra={"example": "Notification"})
    planned_date: date = Field(..., json_schema_extra={"example": "2025-10-15"})
    actual_date: Optional[date] = Field(default=None, json_schema_extra={"example": "2025-10-20"})
    status: MilestoneStatusEnum = Field(default=MilestoneStatusEnum.PENDING)


class MilestoneUpdate(BaseModel):
    actual_date: Optional[date] = None
    status: Optional[MilestoneStatusEnum] = None


class MilestoneResponse(BaseModel):
    id: str
    project_id: str
    title: str
    stage: str
    planned_date: date
    actual_date: Optional[date] = None
    status: str
    delay_days: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MilestoneListResponse(BaseModel):
    items: List[MilestoneResponse]
    total: int

