from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PaymentStatusEnum


class CompensationCreate(BaseModel):
    parcel_id: str = Field(..., json_schema_extra={"example": "pcl-uuid-101"})
    assessed_amount_inr: float = Field(..., ge=0.0, json_schema_extra={"example": 4500000.0})
    approved_amount_inr: float = Field(..., ge=0.0, json_schema_extra={"example": 4500000.0})
    disbursed_amount_inr: float = Field(default=0.0, ge=0.0, json_schema_extra={"example": 2000000.0})
    payment_status: PaymentStatusEnum = Field(default=PaymentStatusEnum.ASSESSED)
    payment_date: Optional[date] = Field(default=None, json_schema_extra={"example": "2026-05-12"})


class CompensationUpdate(BaseModel):
    assessed_amount_inr: Optional[float] = Field(default=None, ge=0.0)
    approved_amount_inr: Optional[float] = Field(default=None, ge=0.0)
    disbursed_amount_inr: Optional[float] = Field(default=None, ge=0.0)
    payment_status: Optional[PaymentStatusEnum] = None
    payment_date: Optional[date] = None


class CompensationResponse(BaseModel):
    id: str
    project_id: str
    parcel_id: str
    survey_number: Optional[str] = None
    owner_name: Optional[str] = None
    assessed_amount_inr: float
    approved_amount_inr: float
    disbursed_amount_inr: float
    pending_amount_inr: float
    payment_status: str
    payment_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompensationListResponse(BaseModel):
    items: List[CompensationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

