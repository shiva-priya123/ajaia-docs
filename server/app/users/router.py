from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.users.schemas import UserOut
from app.users.service import get_all_users

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[UserOut]:
    """List all users (used for the share-picker UI)."""
    users = get_all_users(db)
    return [UserOut.model_validate(u) for u in users]
