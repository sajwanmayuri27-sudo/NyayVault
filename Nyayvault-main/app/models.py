import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id(prefix: str) -> str:
    """Short, readable, collision-safe ids e.g. usr_3f9a2b1c."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Enums -- mirrored 1:1 with the values the frontend already hardcodes in
# js/data.js and js/dashboard.js (NAV_CONFIG, ROLE_META, status badges...).
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    io = "io"                # Investigating Officer
    forensic = "forensic"    # Forensic Specialist
    judge = "judge"          # Judge / Court
    admin = "admin"          # Administrator


class UserStatus(str, enum.Enum):
    approved = "approved"
    pending = "pending"


class CaseStatus(str, enum.Enum):
    active = "active"
    court = "court"
    closed = "closed"


class DocType(str, enum.Enum):
    VIDEO = "VIDEO"
    PDF = "PDF"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    OTHER = "OTHER"


class DocStatus(str, enum.Enum):
    pending = "pending"      # uploaded, not yet hash-verified
    verified = "verified"
    tampered = "tampered"


class AuditAction(str, enum.Enum):
    login = "login"
    login_failed = "login_failed"
    logout = "logout"
    upload = "upload"
    view = "view"
    verify = "verify"
    tamper = "tamper"
    download = "download"
    present = "present"
    approve = "approve"
    revoke = "revoke"
    redact = "redact"
    transcribe = "transcribe"
    report = "report"
    search = "search"
    case_create = "case_create"
    user_create = "user_create"
    blockchain_anchor = "blockchain_anchor"
    blockchain_anchor_failed = "blockchain_anchor_failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: gen_id("usr"))
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    badge_id = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")

    @property
    def role_label(self) -> str:
        return {
            "io": "Investigating Officer",
            "forensic": "Forensic Specialist",
            "judge": "Judge / Court",
            "admin": "Administrator",
        }[self.role.value if isinstance(self.role, UserRole) else self.role]


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: gen_id("case"))
    number = Column(String, unique=True, nullable=False, index=True)  # FIR-2026-0341
    title = Column(String, nullable=False)
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.active)
    created_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship(
        "Document", back_populates="case", cascade="all, delete-orphan"
    )

    @property
    def doc_count(self) -> int:
        return len(self.documents)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: gen_id("doc"))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(DocType), nullable=False)
    file_path = Column(String, nullable=False)   # path on disk, relative to STORAGE_DIR
    size_bytes = Column(Integer, default=0)
    content_type = Column(String, nullable=True)

    uploader_id = Column(String, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    hash_sha256 = Column(String, nullable=False)   # hash computed at upload time
    status = Column(Enum(DocStatus), nullable=False, default=DocStatus.pending)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Optional: set once a background task successfully anchors hash_sha256
    # on-chain (see app/utils/blockchain_anchor.py). NULL until then, and
    # stays NULL forever if blockchain anchoring is disabled/unconfigured --
    # this is purely an added proof layer, never a dependency for normal
    # reads/writes of the document record.
    blockchain_tx_hash = Column(String, nullable=True)

    # Metadata extracted at upload time (EXIF for images, best-effort for
    # everything else). Stored as JSON: {device, gps, imei, created}
    exif = Column(JSON, default=dict)

    case = relationship("Case", back_populates="documents")
    uploader = relationship("User", back_populates="documents")

    @property
    def hash_display(self) -> str:
        """Shortened hash for list views, matching the frontend's
        '9f2a1c...4e0b7d' style."""
        h = self.hash_sha256
        return f"{h[:6]}...{h[-6:]}" if len(h) > 14 else h


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: gen_id("log"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    action = Column(Enum(AuditAction), nullable=False)
    detail = Column(Text, nullable=False, default="")
    case_id = Column(String, ForeignKey("cases.id"), nullable=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)

    user = relationship("User", back_populates="audit_logs")
