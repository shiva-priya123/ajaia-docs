from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


def get_all_users(db: Session) -> list[User]:
    """Return all users ordered by name."""
    return db.query(User).order_by(User.name).all()
