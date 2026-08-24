import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, Milestone, Approval
from app.models.parcel import LandParcel
from app.models.compensation import CompensationRecord
from app.models.family import AffectedFamily, RehabilitationRecord
from app.models.geography import State
from app.models.enums import ProjectStatusEnum, ProjectStageEnum, MilestoneStatusEnum, ApprovalStatusEnum
from app.schemas.ai import (
    RiskLevelEnum,
    RecommendationPriorityEnum,
    RiskFactor,
    Recommendation,
    ProjectRiskResponse,
    BottleneckDetail,
    ProjectInsightResponse,
    HighRiskProjectItem,
    AIOverviewResponse,
)

logger = logging.getLogger("lams.ai_decision_support")


def determine_risk_level(score: int) -> RiskLevelEnum:
    if score >= 75:
        return RiskLevelEnum.CRITICAL
    elif score >= 50:
        return RiskLevelEnum.HIGH
    elif score >= 25:
        return RiskLevelEnum.MEDIUM
    return RiskLevelEnum.LOW


async def calculate_project_risk(
    session: AsyncSession, project: Project
) -> Tuple[int, RiskLevelEnum, float, List[RiskFactor], List[Recommendation], List[BottleneckDetail]]:
    """Calculates deterministic, explainable risk score, risk factors, bottlenecks, and recommendations."""

    factors: List[RiskFactor] = []
    recommendations: List[Recommendation] = []
    bottlenecks: List[BottleneckDetail] = []
    total_score = 0

    # ---------------------------------------------------------
    # 1. MILESTONE DELAY SCORE (Max 30 pts)
    # ---------------------------------------------------------
    ms_stmt = select(Milestone).where(Milestone.project_id == project.id)
    ms_res = await session.execute(ms_stmt)
    milestones = ms_res.scalars().all()

    ms_score = 0
    max_delay = max([m.delay_days for m in milestones], default=0)
    overdue_count = sum(1 for m in milestones if m.planned_date < date.today() and not m.actual_date)

    if max_delay >= 60:
        ms_score = 30
        severity = "CRITICAL"
        desc = f"Critical milestone delay detected ({max_delay} days overdue)."
    elif max_delay >= 31:
        ms_score = 22
        severity = "HIGH"
        desc = f"Significant milestone delay detected ({max_delay} days overdue)."
    elif max_delay >= 8:
        ms_score = 14
        severity = "MEDIUM"
        desc = f"Moderate milestone delay detected ({max_delay} days overdue)."
    elif max_delay >= 1 or overdue_count > 0:
        ms_score = 7
        severity = "LOW"
        desc = f"Minor milestone delay or {overdue_count} overdue milestone(s)."
    else:
        severity = "LOW"
        desc = "All milestones are progressing on schedule."

    if ms_score > 0:
        factors.append(
            RiskFactor(
                factor="Milestone Schedule Adherence",
                impact=f"+{ms_score} pts",
                severity=severity,
                description=desc,
                metric="Max Milestone Delay Days",
                current_value=f"{max_delay} days",
                threshold="0 days",
            )
        )
        bottlenecks.append(
            BottleneckDetail(
                category="DELAY",
                title="Milestone Execution Backlog",
                severity=severity,
                description=desc,
                impact_points=ms_score,
            )
        )
        recommendations.append(
            Recommendation(
                priority=RecommendationPriorityEnum.URGENT if ms_score >= 22 else RecommendationPriorityEnum.HIGH,
                title="Escalate Milestone Deadlines",
                description=f"Appoint dedicated nodal officer to resolve {max_delay}-day delay on critical path milestones.",
                related_factor="Milestone Schedule Adherence",
            )
        )

    total_score += ms_score

    # ---------------------------------------------------------
    # 2. PROJECT HEALTH STATUS SCORE (Max 20 pts)
    # ---------------------------------------------------------
    status_score = 0
    p_status = project.status.value if hasattr(project.status, "value") else str(project.status)

    if p_status == "CRITICAL":
        status_score = 20
        severity = "CRITICAL"
        desc = "Project marked as CRITICAL due to severe multi-faceted bottlenecks."
    elif p_status == "DELAYED":
        status_score = 12
        severity = "HIGH"
        desc = "Project marked as DELAYED due to schedule slippage."
    else:
        severity = "LOW"
        desc = "Project health status is ON_TRACK."

    if status_score > 0:
        factors.append(
            RiskFactor(
                factor="Declared Project Status",
                impact=f"+{status_score} pts",
                severity=severity,
                description=desc,
                metric="Project Status",
                current_value=p_status,
                threshold="ON_TRACK",
            )
        )

    total_score += status_score

    # ---------------------------------------------------------
    # 3. LAND ACQUISITION PROGRESS SCORE (Max 15 pts)
    # ---------------------------------------------------------
    prop_ha = float(project.land_proposed_hectares)
    acq_ha = float(project.land_acquired_hectares)
    acq_pct = round((acq_ha / prop_ha * 100.0), 2) if prop_ha > 0 else 100.0
    stage_str = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)

    land_score = 0
    if stage_str in ["Compensation", "Possession", "Rehabilitation & Resettlement", "Completed"] and acq_pct < 50.0:
        land_score = 15
        severity = "CRITICAL"
        desc = f"Advanced stage ({stage_str}) but only {acq_pct}% land acquired."
    elif stage_str in ["Award", "Compensation"] and acq_pct < 30.0:
        land_score = 10
        severity = "HIGH"
        desc = f"Stage ({stage_str}) with low land acquisition completion ({acq_pct}%)."
    elif acq_pct < 15.0 and stage_str != "Proposal":
        land_score = 6
        severity = "MEDIUM"
        desc = f"Overall land acquisition completion is low ({acq_pct}%)."

    if land_score > 0:
        factors.append(
            RiskFactor(
                factor="Land Acquisition Completion",
                impact=f"+{land_score} pts",
                severity=severity,
                description=desc,
                metric="Land Acquired %",
                current_value=f"{acq_pct}% ({acq_ha} / {prop_ha} Ha)",
                threshold=">75%",
            )
        )
        bottlenecks.append(
            BottleneckDetail(
                category="LAND_ACQUISITION",
                title="Cadastral Parcel Acquisition Lag",
                severity=severity,
                description=desc,
                impact_points=land_score,
            )
        )
        recommendations.append(
            Recommendation(
                priority=RecommendationPriorityEnum.HIGH,
                title="Accelerate Field Cadastral Survey & Possession",
                description="Fast-track district revenue survey and field parcel verification to increase land handover rate.",
                related_factor="Land Acquisition Completion",
            )
        )

    total_score += land_score

    # ---------------------------------------------------------
    # 4. COMPENSATION BOTTLENECK SCORE (Max 15 pts)
    # ---------------------------------------------------------
    comp_stmt = select(
        func.coalesce(func.sum(CompensationRecord.assessed_amount_inr), 0.0).label("assessed"),
        func.coalesce(func.sum(CompensationRecord.approved_amount_inr), 0.0).label("approved"),
        func.coalesce(func.sum(CompensationRecord.disbursed_amount_inr), 0.0).label("disbursed"),
    ).where(CompensationRecord.project_id == project.id)

    comp_row = (await session.execute(comp_stmt)).one()
    c_ass = float(comp_row.assessed)
    c_app = float(comp_row.approved)
    c_dis = float(comp_row.disbursed)
    c_pend = max(0.0, c_app - c_dis)
    c_pct = round((c_dis / c_app * 100.0), 2) if c_app > 0 else 0.0

    comp_score = 0
    if c_pend > 10_000_000:
        comp_score = 15
        severity = "CRITICAL"
        desc = f"Large pending compensation treasury balance (₹{(c_pend / 10000000):.2f} Cr approved but undisbursed)."
    elif c_app > 0 and c_pct < 50.0:
        comp_score = 10
        severity = "HIGH"
        desc = f"Compensation disbursement rate is low ({c_pct}% disbursed)."
    elif c_ass > 0 and c_app == 0:
        comp_score = 6
        severity = "MEDIUM"
        desc = "Compensation assessed but awaiting collector award approval."

    if comp_score > 0:
        factors.append(
            RiskFactor(
                factor="Compensation Disbursement Bottleneck",
                impact=f"+{comp_score} pts",
                severity=severity,
                description=desc,
                metric="Undisbursed Approved Compensation",
                current_value=f"₹{(c_pend / 10000000):.2f} Cr",
                threshold="< ₹0.50 Cr",
            )
        )
        bottlenecks.append(
            BottleneckDetail(
                category="COMPENSATION",
                title="Treasury Beneficiary Disbursement Delay",
                severity=severity,
                description=desc,
                impact_points=comp_score,
            )
        )
        recommendations.append(
            Recommendation(
                priority=RecommendationPriorityEnum.HIGH,
                title="Expedite Direct Beneficiary Direct Transfer (DBT)",
                description="Coordinate with District Treasury Officer to process pending compensation awards directly to bank accounts.",
                related_factor="Compensation Disbursement Bottleneck",
            )
        )

    total_score += comp_score

    # ---------------------------------------------------------
    # 5. WORKFLOW / APPROVAL BOTTLENECK SCORE (Max 10 pts)
    # ---------------------------------------------------------
    appr_stmt = select(Approval).where(Approval.project_id == project.id)
    approvals = (await session.execute(appr_stmt)).scalars().all()

    has_rejected = any(a.status == ApprovalStatusEnum.REJECTED or a.status == "REJECTED" for a in approvals)
    pending_count = sum(1 for a in approvals if a.status == ApprovalStatusEnum.PENDING or a.status == "PENDING")

    wf_score = 0
    if has_rejected:
        wf_score = 10
        severity = "HIGH"
        desc = "One or more stage transition approval requests have been REJECTED."
    elif pending_count > 0:
        wf_score = 5
        severity = "MEDIUM"
        desc = f"{pending_count} pending workflow approval request(s) awaiting executive sign-off."

    if wf_score > 0:
        factors.append(
            RiskFactor(
                factor="Administrative Approval Bottleneck",
                impact=f"+{wf_score} pts",
                severity=severity,
                description=desc,
                metric="Pending / Rejected Approvals",
                current_value=f"{pending_count} pending, rejected={has_rejected}",
                threshold="0 pending/rejected",
            )
        )
        bottlenecks.append(
            BottleneckDetail(
                category="WORKFLOW",
                title="Inter-Departmental Sign-Off Clearance",
                severity=severity,
                description=desc,
                impact_points=wf_score,
            )
        )
        recommendations.append(
            Recommendation(
                priority=RecommendationPriorityEnum.MEDIUM,
                title="Review Rejected / Pending Approvals",
                description="Address administrative objection remarks and resubmit clearance paperwork for stage transition.",
                related_factor="Administrative Approval Bottleneck",
            )
        )

    total_score += wf_score

    # ---------------------------------------------------------
    # 6. R&R (REHABILITATION & RESETTLEMENT) SCORE (Max 10 pts)
    # ---------------------------------------------------------
    fam_stmt = select(
        func.count(AffectedFamily.id).label("total"),
        func.coalesce(func.sum(case((AffectedFamily.is_displaced.is_(True), 1), else_=0)), 0).label("displaced"),
    ).where(AffectedFamily.project_id == project.id)
    fam_row = (await session.execute(fam_stmt)).one()
    t_disp = fam_row.displaced or 0

    rr_stmt = select(
        func.coalesce(func.sum(case((RehabilitationRecord.resettlement_status == "COMPLETED", 1), else_=0)), 0).label("resettled"),
    ).where(RehabilitationRecord.project_id == project.id)
    rr_row = (await session.execute(rr_stmt)).one()
    t_res = rr_row.resettled or 0

    rr_score = 0
    if t_disp > 0 and t_res == 0:
        rr_score = 10
        severity = "HIGH"
        desc = f"{t_disp} displaced families identified but 0 completed resettlement packages."
    elif t_disp > 0 and (t_res / t_disp) < 0.5:
        rr_score = 6
        severity = "MEDIUM"
        desc = f"R&R completion is low ({t_res} / {t_disp} displaced families resettled)."

    if rr_score > 0:
        factors.append(
            RiskFactor(
                factor="Rehabilitation & Resettlement (R&R) Progress",
                impact=f"+{rr_score} pts",
                severity=severity,
                description=desc,
                metric="Resettled / Displaced Families",
                current_value=f"{t_res} / {t_disp}",
                threshold="100%",
            )
        )
        bottlenecks.append(
            BottleneckDetail(
                category="RR",
                title="Displaced Family Resettlement Infrastructure",
                severity=severity,
                description=desc,
                impact_points=rr_score,
            )
        )
        recommendations.append(
            Recommendation(
                priority=RecommendationPriorityEnum.HIGH,
                title="Finalize R&R Colony Allotments",
                description="Complete housing site development and disburse resettlement grant allowances to displaced families.",
                related_factor="Rehabilitation & Resettlement (R&R) Progress",
            )
        )

    total_score += rr_score

    # Final Risk Normalization
    final_score = min(100, total_score)
    risk_level = determine_risk_level(final_score)

    # Calculate Confidence Score (0.0 to 1.0)
    conf = 0.40
    if len(milestones) > 0:
        conf += 0.15
    if prop_ha > 0:
        conf += 0.15
    if c_ass > 0 or c_app > 0:
        conf += 0.15
    if fam_row.total > 0:
        conf += 0.13
    confidence = min(0.98, round(conf, 2))

    if not recommendations:
        recommendations.append(
            Recommendation(
                priority=RecommendationPriorityEnum.LOW,
                title="Maintain Schedule Monitoring",
                description="Project indicators are currently within acceptable operational parameters. Continue standard monitoring.",
                related_factor="General Operations",
            )
        )

    return final_score, risk_level, confidence, factors, recommendations, bottlenecks


async def get_project_risk_analysis(session: AsyncSession, project: Project) -> ProjectRiskResponse:
    score, level, confidence, factors, recs, _ = await calculate_project_risk(session, project)
    return ProjectRiskResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.name,
        risk_score=score,
        risk_level=level,
        confidence=confidence,
        factors=factors,
        recommendations=recs,
        generated_at=datetime.now(timezone.utc),
    )


async def get_project_insights_analysis(session: AsyncSession, project: Project) -> ProjectInsightResponse:
    score, level, _, _, recs, bottlenecks = await calculate_project_risk(session, project)
    summary = f"Project '{project.name}' has a risk score of {score}/100 ({level.value}). "
    if bottlenecks:
        summary += f"Primary bottlenecks identified in {', '.join([b.category for b in bottlenecks])}."
    else:
        summary += "No critical operational bottlenecks detected."

    return ProjectInsightResponse(
        project_id=project.id,
        project_name=project.name,
        risk_score=score,
        risk_level=level,
        bottlenecks=bottlenecks,
        recommendations=recs,
        summary=summary,
    )


async def generate_ai_overview(session: AsyncSession, projects: List[Project]) -> AIOverviewResponse:
    """Generates national AI decision-support overview across projects."""
    total_projects = len(projects)
    low_cnt = 0
    med_cnt = 0
    high_cnt = 0
    crit_cnt = 0
    scores: List[int] = []
    items: List[Tuple[int, HighRiskProjectItem]] = []

    for p in projects:
        score, level, _, factors, recs, _ = await calculate_project_risk(session, p)
        scores.append(score)

        if level == RiskLevelEnum.LOW:
            low_cnt += 1
        elif level == RiskLevelEnum.MEDIUM:
            med_cnt += 1
        elif level == RiskLevelEnum.HIGH:
            high_cnt += 1
        elif level == RiskLevelEnum.CRITICAL:
            crit_cnt += 1

        top_factor = factors[0].factor if factors else "Optimal Progress"
        rec_action = recs[0].title if recs else "Continue Standard Monitoring"

        state_name = p.state.name if hasattr(p, "state") and p.state else str(p.state_id)
        cat_str = p.category.value if hasattr(p.category, "value") else str(p.category)
        stage_str = p.current_stage.value if hasattr(p.current_stage, "value") else str(p.current_stage)

        item = HighRiskProjectItem(
            project_id=p.id,
            project_code=p.project_code,
            project_name=p.name,
            state=state_name,
            category=cat_str,
            current_stage=stage_str,
            risk_score=score,
            risk_level=level,
            top_risk_factor=top_factor,
            recommended_action=rec_action,
        )
        items.append((score, item))

    # Sort descending by risk score
    items.sort(key=lambda x: x[0], reverse=True)
    highest_risk = [x[1] for x in items[:5]]
    avg_score = round(sum(scores) / total_projects, 1) if total_projects > 0 else 0.0

    insights = [
        f"{crit_cnt + high_cnt} out of {total_projects} projects require urgent executive intervention.",
        f"National average decision-support risk index stands at {avg_score}/100.",
        "Primary risk drivers across national infrastructure corridors are milestone schedule slippage and compensation disbursement bottlenecks.",
    ]

    return AIOverviewResponse(
        total_projects=total_projects,
        low_risk_projects=low_cnt,
        medium_risk_projects=med_cnt,
        high_risk_projects=high_cnt,
        critical_projects=crit_cnt,
        average_risk_score=avg_score,
        highest_risk_projects=highest_risk,
        national_insights=insights,
    )

