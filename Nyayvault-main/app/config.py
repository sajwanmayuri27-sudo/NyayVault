import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # --- General ---
    APP_NAME: str = "NyayVault API"
    APP_VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "development")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'nyayvault.db'}"
    )

    # --- Auth / JWT ---
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev-secret-key-change-this-in-production-please"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")  # 8 hour shift
    )

    # --- File storage ---
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
    EVIDENCE_DIR: Path = STORAGE_DIR / "evidence"
    REPORTS_DIR: Path = STORAGE_DIR / "reports"
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "250"))

    # --- CORS ---
    # Comma-separated list of allowed origins. "*" for local/demo use.
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")


settings = Settings()

settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
