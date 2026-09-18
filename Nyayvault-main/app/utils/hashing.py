import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1MB


def sha256_of_file(path: Path) -> str:
    """Stream a file through SHA-256 so large evidence files (video) don't
    have to be loaded into memory at once."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()
