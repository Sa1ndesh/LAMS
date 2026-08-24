import logging
from datetime import date
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, Milestone
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.models.enums import MilestoneStatusEnum, ProjectStatusEnum, NotificationTypeEnum

logger = logging.getLogger("lams.delay_engine")


async def evaluate_project_delays(
    session: AsyncSession,
    project_id: str,
    create_notifications: bool = True,
) -> Tuple[int, ProjectStatusEnum]:
    """
    Evaluates milestones for a project, calculates delay_days, updates milestone statuses,
    updates overall project status (ON_TRACK -> DELAYED -> CRITICAL), and creates Notifications/AuditLogs.
    Returns tuple: (max_delay_days, new_project_status)
    """
    today = date.today()

    proj_res = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.milestones))
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        return 0, ProjectStatusEnum.ON_TRACK

    max_delay = 0
    delayed_milestone_titles: List[str] = []

    for m in project.milestones:
        delay = 0
        is_delayed = False

        if m.actual_date and m.actual_date > m.planned_date:
            delay = (m.actual_date - m.planned_date).days
            is_delayed = True
        elif not m.actual_date and m.planned_date < today:
            delay = (today - m.planned_date).days
            is_delayed = True

        m.delay_days = max(0, delay)

        if is_delayed and delay > 0:
            m.status = MilestoneStatusEnum.DELAYED
            max_delay = max(max_delay, delay)
            delayed_milestone_titles.append(m.title)
        elif m.actual_date and m.actual_date <= m.planned_date:
            m.status = MilestoneStatusEnum.COMPLETED
        elif m.status == MilestoneStatusEnum.DELAYED and not is_delayed:
            m.status = MilestoneStatusEnum.PENDING

    # Determine Project Status
    old_status = project.status
    if max_delay > 30:
        new_status = ProjectStatusEnum.CRITICAL
    elif max_delay > 0:
        new_status = ProjectStatusEnum.DELAYED
    elif project.current_stage.value == "Completed" if hasattr(project.current_stage, "value") else str(project.current_stage) == "Completed":
        new_status = ProjectStatusEnum.COMPLETED
    else:
        new_status = ProjectStatusEnum.ON_TRACK

    project.status = new_status

    # Generate Notification & AuditLog if status worsened or delays found
    if create_notifications and max_delay > 0 and (old_status != new_status or delayed_milestone_titles):
        title = f"Project Delay Alert: {project.name}"
        msg = f"Project status updated to {new_status.value}. Max delay of {max_delay} days detected across {len(delayed_milestone_titles)} milestone(s)."

        # Avoid duplicate unread notification with same title
        dup_res = await session.execute(
            select(Notification).where(
                Notification.project_id == project.id,
                Notification.title == title,
                Notification.is_read.is_(False),
            )
        )
        if not dup_res.scalar_one_or_none():
            notif = Notification(
                project_id=project.id,
                notification_type=NotificationTypeEnum.MILESTONE_DELAY,
                title=title,
                message=msg,
                is_read=False,
            )
            session.add(notif)

            audit_action = "PROJECT_CRITICAL" if new_status == ProjectStatusEnum.CRITICAL else "PROJECT_DELAYED"
            audit = AuditLog(
                user_id=None,
                entity_type="PROJECT",
                entity_id=project.id,
                action=audit_action,
                old_value={"status": old_status.value if hasattr(old_status, "value") else str(old_status)},
                new_value={"status": new_status.value, "max_delay_days": max_delay},
            )
            session.add(audit)

    await session.flush()
    return max_delay, new_status

