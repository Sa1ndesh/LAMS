from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ProjectStageEnum, ApprovalStatusEnum


class WorkflowTransitionRequest(BaseModel):
    target_stage: str = Field(..., json_schema_extra={"example": "VERIFICATION"})
    remarks: Optional[str] = Field(None, max_length=1000, json_schema_extra={"example": "Verification completed by Land Acquisition Officer"})
    is_override: Optional[bool] = Field(False, json_schema_extra={"example": False})


class ApprovalActionRequest(BaseModel):
    remarks: Optional[str] = Field(None, max_length=1000, json_schema_extra={"example": "Approved by District Collector"})


class ApprovalResponse(BaseModel):
    id: str
    project_id: str
    stage: str
    requested_by: str
    approved_by: Optional[str] = None
    status: str
    remarks: Optional[str] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalListResponse(BaseModel):
    items: List[ApprovalResponse]
    total: int


class WorkflowHistoryItem(BaseModel):
    id: str
    project_id: str
    previous_stage: Optional[str] = None
    new_stage: str
    action: str
    user: str
    role: Optional[str] = None
    remarks: Optional[str] = None
    approval_status: Optional[str] = None
    timestamp: datetime


class WorkflowHistoryResponse(BaseModel):
    project_id: str
    current_stage: str
    status: str
    history: List[WorkflowHistoryItem]
    pending_approval: Optional[ApprovalResponse] = None

