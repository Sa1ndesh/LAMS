from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationPriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RiskFactor(BaseModel):
    factor: str
    impact: str  # e.g., "+25 pts"
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    metric: str
    current_value: Any
    threshold: Any


class Recommendation(BaseModel):
    priority: RecommendationPriorityEnum
    title: str
    description: str
    related_factor: str


class ProjectRiskResponse(BaseModel):
    project_id: str
    project_code: str
    project_name: str
    risk_score: int  # 0 to 100
    risk_level: RiskLevelEnum
    confidence: float  # 0.0 to 1.0
    factors: List[RiskFactor]
    recommendations: List[Recommendation]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BottleneckDetail(BaseModel):
    category: str  # DELAY, COMPENSATION, LAND_ACQUISITION, WORKFLOW, RR
    title: str
    severity: str
    description: str
    impact_points: int


class ProjectInsightResponse(BaseModel):
    project_id: str
    project_name: str
    risk_score: int
    risk_level: RiskLevelEnum
    bottlenecks: List[BottleneckDetail]
    recommendations: List[Recommendation]
    summary: str


class HighRiskProjectItem(BaseModel):
    project_id: str
    project_code: str
    project_name: str
    state: str
    category: str
    current_stage: str
    risk_score: int
    risk_level: RiskLevelEnum
    top_risk_factor: str
    recommended_action: str


class AIOverviewResponse(BaseModel):
    total_projects: int
    low_risk_projects: int
    medium_risk_projects: int
    high_risk_projects: int
    critical_projects: int
    average_risk_score: float
    highest_risk_projects: List[HighRiskProjectItem]
    national_insights: List[str]

