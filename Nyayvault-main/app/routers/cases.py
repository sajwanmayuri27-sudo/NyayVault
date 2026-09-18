from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_client_ip, get_current_user, log_audit, require_roles
from app.models import AuditAction, Case, User
from app.schemas import CaseCreate, CaseDetailOut, CaseOut, OverviewOut, PresentSessionOut

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CaseOut])
def list_cases(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """All approved roles can see the case list (io/forensic work cases,
    judges see the docket, admins see counts on the overview)."""
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.post("", response_model=CaseOut, status_code=201)
def create_case(
    payload: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("io")),
):
    if db.query(Case).filter(Case.number == payload.number).first():
        raise HTTPException(400, "A case with this FIR number already exists.")

    case = Case(
        number=payload.number,
        title=payload.title,
        status=payload.status,
        created_by_id=user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    log_audit(
        db,
        action=AuditAction.case_create,
        detail=f"'{user.username}' opened case {case.number} — {case.title}",
        user=user,
        ip_address=get_client_ip(request),
        case_id=case.id,
    )
    return case


@router.get("/overview/summary", response_model=OverviewOut)
def overview(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    from app.models import AuditLog, Document, DocStatus, CaseStatus

    active_cases = db.query(Case).filter(Case.status == CaseStatus.active).count()
    pending = db.query(Document).filter(Document.status != DocStatus.verified).count()
    evidence_items = db.query(Document).count()
    audit_events = db.query(AuditLog).count()
    return OverviewOut(
        active_cases=active_cases,
        pending_verification=pending,
        evidence_items=evidence_items,
        audit_events=audit_events,
    )


@router.get("/{case_id}", response_model=CaseDetailOut)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found.")
    return case

@router.post("/{case_id}/present", response_model=PresentSessionOut)
def present_in_court(
    case_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("judge")),
):
    """Logs (and timestamps) a courtroom presentation session. The frontend
    renders the watermark client-side; the backend is the source of truth
    for who presented what, and when, for the audit trail."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found.")

    now = datetime.now(timezone.utc)
    watermark = f"PRESENTED BY {user.username.upper()} · {user.role_label.upper()}"

    log_audit(
        db,
        action=AuditAction.present,
        detail=f"'{user.username}' presented case {case.number} in courtroom view",
        user=user,
        ip_address=get_client_ip(request),
        case_id=case.id,
    )
    return PresentSessionOut(
        case_id=case.id, watermark_text=watermark, presented_by=user.full_name, presented_at=now
    )
