from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.shares.schemas import ShareCreate, ShareOut, ShareUpdate
from app.shares.service import (
    create_share,
    delete_share,
    get_share_by_id,
    get_shares_for_document,
    update_share_permission,
)
from app.utils.exceptions import bad_request, forbidden, not_found
from app.documents.service import get_document_by_id

router = APIRouter(prefix="/api/documents", tags=["shares"])


@router.get("/{document_id}/shares", response_model=list[ShareOut])
def list_shares(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ShareOut]:
    """List all shares for a document (owner only)."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")
    if doc.owner_id != current_user.id:
        raise forbidden("Only the owner can view shares")

    shares = get_shares_for_document(db, document_id)
    return [
        ShareOut(
            id=s.id,
            document_id=s.document_id,
            user_id=s.user_id,
            user_name=s.user.name if s.user else "",
            user_email=s.user.email if s.user else "",
            permission=s.permission,
            created_at=s.created_at,
        )
        for s in shares
    ]


@router.post("/{document_id}/shares", response_model=ShareOut, status_code=201)
def add_share(
    document_id: str,
    body: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShareOut:
    """Share a document with another user (owner only)."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")
    if doc.owner_id != current_user.id:
        raise forbidden("Only the owner can share a document")

    if body.user_id == current_user.id:
        raise bad_request("Cannot share a document with yourself")

    # Check if user exists
    target_user = db.query(User).filter(User.id == body.user_id).first()
    if target_user is None:
        raise not_found("User not found")

    # Check for existing share
    existing = get_shares_for_document(db, document_id)
    for s in existing:
        if s.user_id == body.user_id:
            raise bad_request("Document is already shared with this user")

    share = create_share(db, document_id=document_id, user_id=body.user_id, permission=body.permission)
    return ShareOut(
        id=share.id,
        document_id=share.document_id,
        user_id=share.user_id,
        user_name=target_user.name,
        user_email=target_user.email,
        permission=share.permission,
        created_at=share.created_at,
    )


@router.patch("/{document_id}/shares/{share_id}", response_model=ShareOut)
def change_share_permission(
    document_id: str,
    share_id: str,
    body: ShareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShareOut:
    """Change a collaborator's permission (owner only)."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")
    if doc.owner_id != current_user.id:
        raise forbidden("Only the owner can change sharing")

    share = get_share_by_id(db, share_id)
    if share is None or share.document_id != document_id:
        raise not_found("Share not found")

    share = update_share_permission(db, share, body.permission)
    return ShareOut(
        id=share.id,
        document_id=share.document_id,
        user_id=share.user_id,
        user_name=share.user.name if share.user else "",
        user_email=share.user.email if share.user else "",
        permission=share.permission,
        created_at=share.created_at,
    )


@router.delete("/{document_id}/shares/{share_id}", status_code=204, response_model=None)
def remove_share(
    document_id: str,
    share_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a share from a document (owner only)."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise not_found("Document not found")
    if doc.owner_id != current_user.id:
        raise forbidden("Only the owner can remove shares")

    share = get_share_by_id(db, share_id)
    if share is None or share.document_id != document_id:
        raise not_found("Share not found")

    delete_share(db, share)
