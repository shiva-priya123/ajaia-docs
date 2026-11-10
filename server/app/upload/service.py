from __future__ import annotations

from fastapi import UploadFile

from app.config import settings
from app.utils.exceptions import bad_request, payload_too_large

_CHUNK = 64 * 1024


async def read_upload(file: UploadFile, max_bytes: int | None = None) -> bytes:
    """Read an uploaded file into memory, enforcing a size cap.

    The raw file is intentionally *not* persisted: the product flow is
    "import a file as a new document", so the converted content stored in the
    database is the source of truth. Keeping raw uploads around would only add
    storage to secure and clean up.
    """
    limit = max_bytes if max_bytes is not None else settings.MAX_UPLOAD_BYTES
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(_CHUNK):
        total += len(chunk)
        if total > limit:
            raise payload_too_large(f"File is too large. Maximum size is {limit // (1024 * 1024)} MB.")
        chunks.append(chunk)
    if total == 0:
        raise bad_request("The uploaded file is empty.")
    return b"".join(chunks)
