from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.dependencies import get_client_ip, get_current_user, log_audit, require_roles
from app.models import AuditAction, AuditLog, Case, DocStatus, Document, User
from app.schemas import DocumentOut, VerifyResult
from app.utils.blockchain_anchor import AlreadyAnchoredError, BlockchainAnchorError, anchor_hash_to_blockchain
from app.utils.exif_utils import classify_doc_type, extract_metadata
from app.utils.hashing import sha256_of_file

router = APIRouter(prefix="/api/documents", tags=["documents"])
cases_router = APIRouter(prefix="/api/cases", tags=["documents"])

MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _anchor_hash_in_background(document_id: str, case_id: str, sha256_hex: str) -> None:
    """
    Runs *after* the upload response has already been sent (see
    `background_tasks.add_task(...)` below). Deliberately isolated from the
    request lifecycle:

      - Opens its own short-lived DB session -- the request-scoped one from
        Depends(get_db) is already closed by the time this runs.
      - Never raises. A slow or unreachable blockchain node can delay when
        `blockchain_tx_hash` gets filled in, but it can never fail, slow
        down, or roll back the upload itself, and it never touches file
        storage.
      - Writes exactly one audit log row recording the outcome (success,
        already-anchored, or skipped/failed), same as every other action in
        this app.
    """
    db = SessionLocal()
    try:
        try:
            tx_hash = anchor_hash_to_blockchain(sha256_hex)
        except AlreadyAnchoredError as exc:
            db.add(AuditLog(
                action=AuditAction.blockchain_anchor,
                detail=f"Hash for document {document_id} was already anchored on-chain: {exc}",
                case_id=case_id,
                document_id=document_id,
            ))
            db.commit()
            return
        except BlockchainAnchorError as exc:
            db.add(AuditLog(
                action=AuditAction.blockchain_anchor_failed,
                detail=f"Blockchain anchoring skipped for document {document_id}: {exc}",
                case_id=case_id,
                document_id=document_id,
            ))
            db.commit()
            return

        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.blockchain_tx_hash = tx_hash
        db.add(AuditLog(
            action=AuditAction.blockchain_anchor,
            detail=f"Hash for document {document_id} anchored on-chain (tx {tx_hash})",
            case_id=case_id,
            document_id=document_id,
        ))
        db.commit()
    finally:
        db.close()


@cases_router.get("/{case_id}/documents", response_model=list[DocumentOut])
def list_case_documents(
    case_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found.")
    return case.documents


@cases_router.post("/{case_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    case_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("io", "forensic")),
    file: UploadFile = File(...),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found.")

    doc_type = classify_doc_type(file.filename, file.content_type)

    case_dir: Path = settings.EVIDENCE_DIR / case.id
    case_dir.mkdir(parents=True, exist_ok=True)

    # Namespace the file on disk so two uploads with the same filename never
    # collide, while keeping the human-readable name for display/reports.
    from app.models import gen_id

    doc_id = gen_id("doc")
    safe_name = Path(file.filename).name
    dest_path = case_dir / f"{doc_id}__{safe_name}"

    size = 0
    with open(dest_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest_path.unlink(missing_ok=True)
                raise HTTPException(
                    413, f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit."
                )
            out.write(chunk)

    file_hash = sha256_of_file(dest_path)
    metadata = extract_metadata(dest_path, doc_type)

    document = Document(
        id=doc_id,
        case_id=case.id,
        name=safe_name,
        type=doc_type,
        file_path=str(dest_path.relative_to(settings.STORAGE_DIR)),
        size_bytes=size,
        content_type=file.content_type,
        uploader_id=user.id,
        hash_sha256=file_hash,
        status=DocStatus.verified,  # hash captured fresh at upload time
        last_verified_at=datetime.now(timezone.utc),
        exif=metadata,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    log_audit(
        db,
        action=AuditAction.upload,
        detail=f"'{user.username}' uploaded {document.name} to {case.number}",
        user=user,
        ip_address=get_client_ip(request),
        case_id=case.id,
        document_id=document.id,
    )

    # Fire-and-forget: scheduled to run after this response is sent, on its
    # own DB session. Anchoring status/tx_hash is picked up whenever the
    # document is next fetched (GET /api/documents/{id}) -- the upload
    # response itself never waits on the chain.
    background_tasks.add_task(
        _anchor_hash_in_background, document.id, case.id, document.hash_sha256
    )

    return document


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")

    log_audit(
        db,
        action=AuditAction.view,
        detail=f"'{user.username}' opened {doc.name}",
        user=user,
        ip_address=get_client_ip(request),
        case_id=doc.case_id,
        document_id=doc.id,
    )
    return doc


@router.get("/{document_id}/blockchain")
def get_blockchain_anchor_status(
    document_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Live, read-only chain lookup -- independent of the `blockchain_tx_hash`
    column, which just remembers the tx we sent. This calls the contract
    directly so the result can't drift from on-chain truth, and costs no
    gas (view call).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")

    from app.utils.blockchain_anchor import BlockchainAnchorError, get_anchor_record

    try:
        record = get_anchor_record(doc.hash_sha256)
    except BlockchainAnchorError as exc:
        return {
            "document_id": doc.id,
            "hash_sha256": doc.hash_sha256,
            "blockchain_tx_hash": doc.blockchain_tx_hash,
            "on_chain": None,
            "detail": str(exc),
        }

    return {
        "document_id": doc.id,
        "hash_sha256": doc.hash_sha256,
        "blockchain_tx_hash": doc.blockchain_tx_hash,
        "on_chain": {
            "anchored": record.exists,
            "anchored_by": record.anchored_by if record.exists else None,
            "timestamp": record.timestamp if record.exists else None,
        },
    }


@router.post("/{document_id}/verify", response_model=VerifyResult)
def verify_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("forensic")),
):
    """Recomputes the SHA-256 of the file currently on disk and compares it
    against the hash captured at upload time -- a real integrity check, not
    a simulated one."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")

    file_path = settings.STORAGE_DIR / doc.file_path
    if not file_path.exists():
        raise HTTPException(410, "Evidence file is missing from storage.")

    current_hash = sha256_of_file(file_path)
    match = current_hash == doc.hash_sha256
    doc.status = DocStatus.verified if match else DocStatus.tampered
    doc.last_verified_at = datetime.now(timezone.utc)
    db.commit()

    log_audit(
        db,
        action=AuditAction.verify if match else AuditAction.tamper,
        detail=(
            f"Integrity check on {doc.name}: "
            + ("hash match, verified" if match else "HASH MISMATCH — possible tampering")
        ),
        user=user,
        ip_address=get_client_ip(request),
        case_id=doc.case_id,
        document_id=doc.id,
    )
    return VerifyResult(
        document_id=doc.id,
        status=doc.status,
        hash_at_upload=doc.hash_sha256,
        hash_now=current_hash,
        match=match,
        checked_at=doc.last_verified_at,
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")

    file_path = settings.STORAGE_DIR / doc.file_path
    if not file_path.exists():
        raise HTTPException(410, "Evidence file is missing from storage.")

    log_audit(
        db,
        action=AuditAction.download,
        detail=f"'{user.username}' downloaded {doc.name}",
        user=user,
        ip_address=get_client_ip(request),
        case_id=doc.case_id,
        document_id=doc.id,
    )
    return FileResponse(
        path=file_path, filename=doc.name, media_type=doc.content_type or "application/octet-stream"
    )
