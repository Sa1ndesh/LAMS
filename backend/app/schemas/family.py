from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import SocialCategoryEnum, RRStatusEnum


class FamilyCreate(BaseModel):
    family_reference_id: Optional[str] = Field(default=None, json_schema_extra={"example": "FAM-KA-2026-090"})
    head_of_family: str = Field(..., min_length=2, max_length=150, json_schema_extra={"example": "Rameshwar Rao"})
    village: str = Field(..., json_schema_extra={"example": "Whitefield"})
    family_members_count: int = Field(default=4, ge=1, json_schema_extra={"example": 4})
    category: SocialCategoryEnum = Field(default=SocialCategoryEnum.OBC)
    is_affected: bool = Field(default=True)
    is_displaced: bool = Field(default=True)
    rr_status: RRStatusEnum = Field(default=RRStatusEnum.ELIGIBLE)


class FamilyUpdate(BaseModel):
    head_of_family: Optional[str] = Field(default=None, min_length=2, max_length=150)
    village: Optional[str] = None
    family_members_count: Optional[int] = Field(default=None, ge=1)
    category: Optional[SocialCategoryEnum] = None
    is_displaced: Optional[bool] = None
    rr_status: Optional[RRStatusEnum] = None


class FamilyResponse(BaseModel):
    id: str
    project_id: str
    family_reference_id: str
    head_of_family: str
    village: str
    family_members_count: int
    category: str
    is_affected: bool
    is_displaced: bool
    rr_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyListResponse(BaseModel):
    items: List[FamilyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

