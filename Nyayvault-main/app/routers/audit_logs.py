from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import AuditLog, User
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    case_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Admins (auditlogs section) get the full, unscoped log.
    Judges (timeline section) may only pull logs scoped to a specific case --
    they should not see department-wide activity.
    IO/forensic have no nav entry for this in the frontend, so we simply
    require a case_id from them too.
    """
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    q = db.query(AuditLog).order_by(AuditLog.timestamp.desc())

    if role_value != "admin":
        if not case_id:
            case_id = "__none__"  # non-admins must scope to a case
        q = q.filter(AuditLog.case_id == case_id)
    elif case_id:
        q = q.filter(AuditLog.case_id == case_id)

    return q.limit(limit).all()
