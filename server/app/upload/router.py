from __future__ import annotations

import os

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.documents.schemas import TITLE_MAX_LENGTH
from app.documents.service import create_document
from app.models import User
from app.upload.converter import SUPPORTED_EXTENSIONS, ConversionError, convert_file_to_tiptap_json
from app.upload.schemas import UploadResponse
from app.upload.service import read_upload
from app.utils.exceptions import bad_request

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """Import a .txt, .md or .docx file as a new document owned by the current user."""
    # basename() guards against path components in client-supplied names.
    filename = os.path.basename((file.filename or "").replace("\\", "/")).strip()
    stem, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        shown = ext or "(none)"
        raise bad_request(
            f"Unsupported file type '{shown}'. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    raw_bytes = await read_upload(file)

    try:
        tiptap_json = convert_file_to_tiptap_json(raw_bytes, filename)
    except ConversionError as exc:
        raise bad_request(str(exc)) from exc

    title = stem.strip()[:TITLE_MAX_LENGTH] or "Untitled"
    doc = create_document(db, title=title, owner_id=current_user.id, content=tiptap_json)

    return UploadResponse(
        document_id=doc.id,
        title=doc.title,
        message=f"Successfully imported '{filename}' as a new document.",
    )
