import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationListResponse

logger = logging.getLogger("lams.api.notifications")
router = APIRouter(tags=["Notifications"])


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    project_id: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    unread: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List system and user notifications with optional query filtering."""
    stmt = select(Notification).where(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    )

    if project_id:
        stmt = stmt.where(Notification.project_id == project_id)

    if notification_type:
        stmt = stmt.where(Notification.notification_type == notification_type)

    if unread is True:
        stmt = stmt.where(Notification.is_read.is_(False))
    elif unread is False:
        stmt = stmt.where(Notification.is_read.is_(True))

    stmt = stmt.order_by(Notification.created_at.desc())

    res = await session.execute(stmt)
    notifs = res.scalars().all()

    unread_stmt = (
        select(func.count())
        .select_from(Notification)
        .where(
            ((Notification.user_id == current_user.id) | (Notification.user_id.is_(None))),
            Notification.is_read.is_(False),
        )
    )
    unread_count = (await session.execute(unread_stmt)).scalar_one()

    items = [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            project_id=n.project_id,
            notification_type=n.notification_type.value if hasattr(n.notification_type, "value") else str(n.notification_type),
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifs
    ]
    return NotificationListResponse(items=items, unread_count=unread_count)


@router.get("/notifications/unread-count")
async def get_unread_count(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Returns number of unread notifications."""
    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(
            ((Notification.user_id == current_user.id) | (Notification.user_id.is_(None))),
            Notification.is_read.is_(False),
        )
    )
    count = (await session.execute(stmt)).scalar_one()
    return {"unread_count": count}


@router.put("/notifications/{id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Mark single notification as read."""
    res = await session.execute(select(Notification).where(Notification.id == id))
    n = res.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    n.is_read = True
    await session.commit()
    await session.refresh(n)

    return NotificationResponse(
        id=n.id,
        user_id=n.user_id,
        project_id=n.project_id,
        notification_type=n.notification_type.value if hasattr(n.notification_type, "value") else str(n.notification_type),
        title=n.title,
        message=n.message,
        is_read=n.is_read,
        created_at=n.created_at,
    )


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    stmt = (
        update(Notification)
        .where(
            ((Notification.user_id == current_user.id) | (Notification.user_id.is_(None))),
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "All notifications marked as read."}
