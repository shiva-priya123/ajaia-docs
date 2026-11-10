from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Document, Share, User


def create_document(db: Session, title: str, owner_id: str, content: str | None = None) -> Document:
    """Create and persist a new document."""
    doc = Document(
        title=title,
        content=content if content else json.dumps({"type": "doc", "content": []}),
        owner_id=owner_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document_by_id(db: Session, document_id: str) -> Document | None:
    """Fetch a single document by its primary key."""
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents_for_user(db: Session, user_id: str) -> list[dict]:
    """Return all documents owned by or shared with the given user.

    Each result dict includes a ``role`` field ("owner", "editor", or "viewer").
    """
    # Owned documents
    owned = db.query(Document).filter(Document.owner_id == user_id).all()
    results: list[dict] = []
    for doc in owned:
        results.append(_doc_to_dict(doc, role="owner"))

    # Shared documents
    shares = (
        db.query(Share)
        .filter(Share.user_id == user_id)
        .all()
    )
    for share in shares:
        doc = share.document
        if doc is not None:
            results.append(_doc_to_dict(doc, role=share.permission))

    return results


def update_document(
    db: Session,
    doc: Document,
    title: str | None = None,
    content: str | None = None,
) -> Document:
    """Update the title and/or content of a document."""
    if title is not None:
        doc.title = title
    if content is not None:
        doc.content = content
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, doc: Document) -> None:
    """Delete a document from the database."""
    db.delete(doc)
    db.commit()


def _doc_to_dict(doc: Document, role: str) -> dict:
    """Convert a Document ORM object to a plain dict with role info."""
    return {
        "id": doc.id,
        "title": doc.title,
        "content": doc.content,
        "owner_id": doc.owner_id,
        "owner_name": doc.owner.name if doc.owner else "",
        "role": role,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }
