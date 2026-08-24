from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class AnalyticsSummaryResponse(BaseModel):
    total_projects: int
    total_land_proposed_hectares: float
    total_land_acquired_hectares: float
    acquisition_percentage: float
    total_compensation_assessed: float
    total_compensation_approved: float
    total_compensation_disbursed: float
    compensation_percentage: float
    total_affected_families: int
    total_displaced_families: int
    total_resettled_families: int
    delayed_projects: int
    critical_projects: int
    completed_projects: int

    model_config = ConfigDict(from_attributes=True)


class StateAnalyticsItem(BaseModel):
    state_id: int
    state_name: str
    project_count: int
    land_proposed_hectares: float
    land_acquired_hectares: float
    acquisition_percentage: float
    compensation_assessed: float
    compensation_disbursed: float
    compensation_percentage: float
    affected_families: int
    displaced_families: int
    delayed_projects: int
    completed_projects: int


class StateAnalyticsListResponse(BaseModel):
    items: List[StateAnalyticsItem]
    total: int


class ProjectAnalyticsItem(BaseModel):
    project_id: str
    project_code: str
    project_name: str
    state: str
    district: str
    category: str
    project_status: str
    current_stage: str
    land_proposed: float
    land_acquired: float
    acquisition_percentage: float
    compensation_assessed: float
    compensation_disbursed: float
    compensation_percentage: float
    affected_families: int
    displaced_families: int
    delay_days: int
    risk_indicator: str


class ProjectAnalyticsListResponse(BaseModel):
    items: List[ProjectAnalyticsItem]
    total: int


class LandAnalyticsGroup(BaseModel):
    group_by: str
    label: str
    proposed_hectares: float
    acquired_hectares: float
    pending_hectares: float
    acquisition_percentage: float


class LandAnalyticsResponse(BaseModel):
    total_proposed: float
    total_acquired: float
    total_pending: float
    overall_percentage: float
    by_state: List[LandAnalyticsGroup]
    by_project: List[LandAnalyticsGroup]
    by_land_type: List[LandAnalyticsGroup]
    by_status: List[LandAnalyticsGroup]


class CompensationAnalyticsGroup(BaseModel):
    group_by: str
    label: str
    assessed_amount: float
    approved_amount: float
    disbursed_amount: float
    pending_amount: float
    disbursement_percentage: float


class CompensationAnalyticsResponse(BaseModel):
    total_assessed: float
    total_approved: float
    total_disbursed: float
    total_pending: float
    overall_percentage: float
    by_project: List[CompensationAnalyticsGroup]
    by_state: List[CompensationAnalyticsGroup]
    by_payment_status: List[CompensationAnalyticsGroup]


class RehabilitationAnalyticsGroup(BaseModel):
    group_by: str
    label: str
    affected_families: int
    displaced_families: int
    identified_families: int
    eligible_families: int
    assistance_disbursed: float
    resettled_families: int


class RehabilitationAnalyticsResponse(BaseModel):
    total_affected: int
    total_displaced: int
    total_resettled: int
    resettlement_percentage: float
    by_state: List[RehabilitationAnalyticsGroup]
    by_project: List[RehabilitationAnalyticsGroup]
    by_social_category: List[RehabilitationAnalyticsGroup]
    by_rr_status: List[RehabilitationAnalyticsGroup]


class TimelineAnalyticsResponse(BaseModel):
    total_milestones: int
    completed_milestones: int
    pending_milestones: int
    delayed_milestones: int
    average_delay_days: float
    max_delay_days: int
    ontime_percentage: float
    by_stage: List[Dict[str, Any]]


class WorkflowAnalyticsResponse(BaseModel):
    stage_distribution: List[Dict[str, Any]]
    pending_approvals: int
    approved_approvals: int
    rejected_approvals: int
    total_approvals: int


class DelayAnalyticsResponse(BaseModel):
    delayed_projects_count: int
    critical_projects_count: int
    total_delayed_milestones: int
    average_project_delay_days: float
    max_project_delay_days: int
    by_state: List[Dict[str, Any]]
    by_category: List[Dict[str, Any]]
    by_stage: List[Dict[str, Any]]

