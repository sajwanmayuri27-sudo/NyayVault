from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Base, engine
from app.routers import audio, audit_logs, auth, cases, documents, redaction, reports, search, users

# Create tables if they don't exist yet. For anything beyond local/demo use,
# swap this for a real migration tool (Alembic) instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend for NyayVault — Digital Evidence Management System. "
        "Handles auth/RBAC, case & evidence records, SHA-256 chain-of-custody "
        "hashing and integrity verification, audit logging, search, PDF "
        "report generation, and best-effort redaction/transcription."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(documents.cases_router)
app.include_router(reports.router)
app.include_router(redaction.router)
app.include_router(audio.router)
app.include_router(search.router)
app.include_router(audit_logs.router)

# Serve uploaded evidence + generated reports directly for convenience in
# local/demo use. In production, put this behind authenticated routes or a
# private object store instead of exposing it as static files.
app.mount("/files", StaticFiles(directory=str(settings.STORAGE_DIR)), name="files")


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


# Serve the frontend from the same FastAPI process so the UI and API are
# connected with no separate web server or CORS setup required.
FRONTEND_DIR = settings.BASE_DIR / "frontend" if hasattr(settings, "BASE_DIR") else None
from pathlib import Path as _Path
FRONTEND_DIR = _Path(__file__).resolve().parent.parent / "frontend"

@app.get("/", include_in_schema=False)
def frontend_login():
    return FileResponse(FRONTEND_DIR / "login.html")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
