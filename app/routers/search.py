from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_client_ip, get_current_user, log_audit
from app.models import AuditAction, Case, Document, User
from app.schemas import SearchResultItem

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SearchResultItem])
def search(
    q: str = Query(..., min_length=1),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Real (if simple) full-text-ish search: matches the query against case
    numbers/titles and evidence file names/hashes. This does NOT search
    inside file contents -- that would need OCR/transcription indexing,
    which is out of scope here (see /documents/{id}/transcribe for audio).
    """
    like = f"%{q}%"
    results: list[SearchResultItem] = []

    cases = db.query(Case).filter(
        or_(Case.number.ilike(like), Case.title.ilike(like))
    ).all()
    for c in cases:
        results.append(
            SearchResultItem(
                case_id=c.id,
                case_number=c.number,
                snippet=f"Case match: {c.title}",
            )
        )

    docs = (
        db.query(Document)
        .filter(or_(Document.name.ilike(like), Document.hash_sha256.ilike(like)))
        .all()
    )
    for d in docs:
        results.append(
            SearchResultItem(
                case_id=d.case_id,
                case_number=d.case.number if d.case else "—",
                document_id=d.id,
                document_name=d.name,
                snippet=f"Evidence match: {d.name} ({d.type.value})",
            )
        )

    if request is not None:
        log_audit(
            db,
            action=AuditAction.search,
            detail=f"'{user.username}' searched for \"{q}\" ({len(results)} results)",
            user=user,
            ip_address=get_client_ip(request),
        )

    return results
