from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Document, Share, User


def create_share(db: Session, document_id: str, user_id: str, permission: str) -> Share:
    """Create a new share record granting a user access to a document."""
    share = Share(document_id=document_id, user_id=user_id, permission=permission)
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


def get_shares_for_document(db: Session, document_id: str) -> list[Share]:
    """Return all shares associated with a document."""
    return db.query(Share).filter(Share.document_id == document_id).all()


def get_share_by_id(db: Session, share_id: str) -> Share | None:
    """Fetch a single share by its primary key."""
    return db.query(Share).filter(Share.id == share_id).first()


def update_share_permission(db: Session, share: Share, permission: str) -> Share:
    """Change the permission level of an existing share."""
    share.permission = permission
    db.commit()
    db.refresh(share)
    return share


def delete_share(db: Session, share: Share) -> None:
    """Remove a share record from the database."""
    db.delete(share)
    db.commit()


def check_document_permission(
    db: Session, document_id: str, user_id: str
) -> str | None:
    """Check what permission a user has on a document.

    Returns "owner" if the user owns the document, the share permission
    ("viewer" or "editor") if shared, or None if no access.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc is None:
        return None
    if doc.owner_id == user_id:
        return "owner"
    share = (
        db.query(Share)
        .filter(Share.document_id == document_id, Share.user_id == user_id)
        .first()
    )
    if share is not None:
        return share.permission
    return None
