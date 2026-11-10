from __future__ import annotations

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response body for a successful file upload."""
    document_id: str
    title: str
    message: str
