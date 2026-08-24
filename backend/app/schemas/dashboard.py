from typing import List, Dict, Any
from pydantic import BaseModel


class StateProgressItem(BaseModel):
    state: str
    target: float
    acquired: float
    percentage: float


class StageDistributionItem(BaseModel):
    stage: str
    count: int


class DashboardSummary(BaseModel):
    total_projects: int
    land_proposed_hectares: float
    land_acquired_hectares: float
    acquisition_percentage: float
    compensation_assessed_inr: float
    compensation_disbursed_inr: float
    compensation_pending_inr: float
    affected_families_count: int
    displaced_families_count: int
    delayed_projects_count: int
    state_progress: List[StateProgressItem]
    stage_distribution: List[StageDistributionItem]

