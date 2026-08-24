from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import DocumentCategoryEnum


class DocumentCreate(BaseModel):
    document_name: str = Field(..., min_length=2, max_length=255, json_schema_extra={"example": "Section 11 Preliminary Notification Gazette"})
    category: DocumentCategoryEnum = Field(..., json_schema_extra={"example": DocumentCategoryEnum.NOTIFICATIONS})
    file_reference: str = Field(..., max_length=500, json_schema_extra={"example": "DOC-GAZETTE-SEC11-001.pdf"})
    uploaded_by: str = Field(default="Central Nodal Officer", json_schema_extra={"example": "District Collector Office"})
    description: Optional[str] = Field(None, max_length=1000)
    version: str = Field(default="1.0", max_length=20)
    status: str = Field(default="Verified", json_schema_extra={"example": "Verified"})


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    document_name: str
    category: str
    file_reference: str
    stored_file_name: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    description: Optional[str] = None
    version: str = "1.0"
    uploaded_by: str
    upload_date: date
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
