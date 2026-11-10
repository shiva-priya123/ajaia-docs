from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.documents.schemas import DocumentCreate, DocumentOut, DocumentUpdate
from app.documents.service import (
    create_document,
    delete_document,
    get_document_by_id,
    get_documents_for_user,
    update_document,
)
from app.models import Share, User
from app.utils.exceptions import conflict, forbidden, not_found
from app.utils.time import as_utc

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentOut]:
    """Return all documents owned by or shared with the current user."""
    docs = get_documents_for_user(db, current_user.id)
    return [DocumentOut(**d) for d in docs]


@router.post("", response_model=DocumentOut, status_code=201)
def create_doc(
    body: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    """Create a new document owned by the current user."""
    doc = create_document(db, title=body.title, owner_id=current_user.id, content=body.content)
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        owner_id=doc.owner_id,
        owner_name=current_user.name,
        role="owner",
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    """Get a single document if the current user has access."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")

    role = _resolve_role(db, doc, current_user)
    if role is None:
        raise forbidden("You do not have access to this document")

    return DocumentOut(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        owner_id=doc.owner_id,
        owner_name=doc.owner.name if doc.owner else "",
        role=role,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.put("/{document_id}", response_model=DocumentOut)
def update_doc(
    document_id: str,
    body: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    """Update a document's title and/or content (owner or editor only)."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")

    role = _resolve_role(db, doc, current_user)
    if role is None:
        raise forbidden("You do not have access to this document")
    if role == "viewer":
        raise forbidden("Viewers cannot edit documents")

    if body.expected_updated_at is not None and as_utc(doc.updated_at) != as_utc(body.expected_updated_at):
        raise conflict(
            "This document was changed by someone else since you opened it. "
            "Reload to get the latest version."
        )

    doc = update_document(db, doc, title=body.title, content=body.content)
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        owner_id=doc.owner_id,
        owner_name=doc.owner.name if doc.owner else "",
        role=role,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.delete("/{document_id}", status_code=204, response_model=None)
def delete_doc(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a document (owner only)."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")

    if doc.owner_id != current_user.id:
        raise forbidden("Only the owner can delete a document")

    delete_document(db, doc)


def _resolve_role(db: Session, doc, current_user: User) -> str | None:
    """Determine the current user's role for the given document.

    Returns "owner", "editor", "viewer", or None if no access.
    """
    if doc.owner_id == current_user.id:
        return "owner"

    share = (
        db.query(Share)
        .filter(Share.document_id == doc.id, Share.user_id == current_user.id)
        .first()
    )
    if share is not None:
        return share.permission

    return None
