from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import UserRole
from app.core.security import utc_now
from app.db.session import get_db
from app.models import AuditLog, LoginHistory, User, UserSession
from app.schemas import Message


router = APIRouter(prefix="/security", tags=["Security"])
admin_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value)


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> list[dict]:
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(100)).all()
    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "ip_address": row.ip_address,
            "details": row.details,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/login-history")
def login_history(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> list[dict]:
    rows = db.scalars(select(LoginHistory).order_by(LoginHistory.id.desc()).limit(100)).all()
    return [
        {
            "id": row.id,
            "email": row.email,
            "ip_address": row.ip_address,
            "success": row.success,
            "reason": row.reason,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/sessions")
def sessions(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> list[dict]:
    rows = db.scalars(select(UserSession).order_by(UserSession.id.desc()).limit(100)).all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "ip_address": row.ip_address,
            "expires_at": row.expires_at,
            "revoked_at": row.revoked_at,
        }
        for row in rows
    ]


@router.post("/sessions/{session_id}/revoke", response_model=Message)
def revoke_session(session_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Message:
    session = db.get(UserSession, session_id)
    if session and not session.revoked_at:
        session.revoked_at = utc_now()
        db.commit()
    return Message(message="Session revoked")


@router.get("/ip-tracking")
def ip_tracking(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    rows = db.execute(select(LoginHistory.ip_address, LoginHistory.email).where(LoginHistory.ip_address.is_not(None))).all()
    ips: dict[str, set[str]] = {}
    for ip_address, email in rows:
        ips.setdefault(ip_address, set()).add(email)
    return {"ip_addresses": {ip: sorted(emails) for ip, emails in ips.items()}}
