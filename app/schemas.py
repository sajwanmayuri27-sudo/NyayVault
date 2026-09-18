from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import AuditAction, CaseStatus, DocStatus, DocType, UserRole, UserStatus


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    username: str
    badge_id: str
    role: UserRole
    status: UserStatus
    created_at: datetime


class UserCreate(BaseModel):
    full_name: str
    username: str
    badge_id: str
    role: UserRole
    password: Optional[str] = Field(
        default=None,
        description="If omitted, a temporary password is generated and returned once.",
    )


class UserCreatedOut(BaseModel):
    user: UserOut
    temporary_password: Optional[str] = None


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
class CaseCreate(BaseModel):
    number: str
    title: str
    status: CaseStatus = CaseStatus.active


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    number: str
    title: str
    status: CaseStatus
    created_at: datetime
    doc_count: int


class CaseDetailOut(CaseOut):
    documents: list["DocumentOut"] = []


# ---------------------------------------------------------------------------
# Documents / Evidence
# ---------------------------------------------------------------------------
class ExifOut(BaseModel):
    device: str = "—"
    gps: str = "—"
    imei: str = "—"
    created: str = "—"


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    name: str
    type: DocType
    size_bytes: int
    uploader_id: Optional[str]
    uploaded_at: datetime
    hash_sha256: str
    hash_display: str
    status: DocStatus
    last_verified_at: Optional[datetime]
    exif: ExifOut


class VerifyResult(BaseModel):
    document_id: str
    status: DocStatus
    hash_at_upload: str
    hash_now: str
    match: bool
    checked_at: datetime


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    user_id: Optional[str]
    role: Optional[str]
    ip_address: Optional[str]
    action: AuditAction
    detail: str
    case_id: Optional[str]
    document_id: Optional[str]


# ---------------------------------------------------------------------------
# Misc feature endpoints (redaction / transcription / search / overview)
# ---------------------------------------------------------------------------
class RedactionResult(BaseModel):
    document_id: str
    kind: str  # "pdf" | "cctv"
    summary: list[str]
    simulated: bool


class TranscriptLine(BaseModel):
    timestamp: str
    text: str


class TranscriptionResult(BaseModel):
    document_id: str
    lines: list[TranscriptLine]
    simulated: bool


class SearchResultItem(BaseModel):
    case_id: str
    case_number: str
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    snippet: str


class OverviewOut(BaseModel):
    active_cases: int
    pending_verification: int
    evidence_items: int
    audit_events: int


class PresentSessionOut(BaseModel):
    case_id: str
    watermark_text: str
    presented_by: str
    presented_at: datetime


# Forward refs used above (TokenResponse.user, CaseDetailOut.documents) are
# defined later in this module -- rebuild once everything exists so FastAPI
# never hits an unresolved ForwardRef at request time.
TokenResponse.model_rebuild()
CaseDetailOut.model_rebuild()

