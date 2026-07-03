from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.db.session import get_db
from app.models import Notification, User
from app.schemas import Message, NotificationCreate, NotificationRead


router = APIRouter(prefix="/notifications", tags=["Notifications"])
staff_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value)


def mock_delivery(notification_id: int, channel: str) -> None:
    print(f"Mock {channel} notification delivered: {notification_id}")


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> Notification:
    notification = Notification(**payload.model_dump())
    db.add(notification)
    db.commit()
    db.refresh(notification)
    background_tasks.add_task(mock_delivery, notification.id, notification.channel)
    return notification


@router.get("", response_model=list[NotificationRead])
def list_notifications(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[Notification]:
    return list(db.scalars(select(Notification).order_by(Notification.id.desc())).all())


@router.post("/{notification_id}/read", response_model=Message)
def mark_read(notification_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Message:
    notification = db.get(Notification, notification_id)
    if notification:
        from app.core.security import utc_now

        notification.read_at = utc_now()
        db.commit()
    return Message(message="Notification marked as read")
