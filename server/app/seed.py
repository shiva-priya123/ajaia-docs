
"""Seed demo users and safely migrate existing demo account identities."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.auth.service import hash_password
from app.models import Document, Share, User

DEMO_PASSWORD = "password123"

DEMO_USERS = [
    {"name": "Shiva", "email": "shiva@example.com"},
    {"name": "Priya", "email": "priya@example.com"},
    {"name": "Sai", "email": "sai@example.com"},
]

# Existing demo identity -> new demo identity.
# Updating the existing User row preserves its ID, password hash,
# document ownership, and sharing permissions.
DEMO_USER_MIGRATIONS = {
    "alice@example.com": {"name": "Shiva", "email": "shiva@example.com"},
    "bob@example.com": {"name": "Priya", "email": "priya@example.com"},
    "charlie@example.com": {"name": "Sai", "email": "sai@example.com"},
}


def _text(text: str, *marks: str) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    if marks:
        node["marks"] = [{"type": mark} for mark in marks]
    return node


def _p(*content: dict[str, Any]) -> dict[str, Any]:
    return {"type": "paragraph", "content": list(content)}


def _h(level: int, text: str) -> dict[str, Any]:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [_text(text)],
    }


def _list(kind: str, *items: str) -> dict[str, Any]:
    return {
        "type": "bulletList" if kind == "ul" else "orderedList",
        "content": [
            {"type": "listItem", "content": [_p(_text(item))]}
            for item in items
        ],
    }


def _doc(*blocks: dict[str, Any]) -> str:
    return json.dumps({"type": "doc", "content": list(blocks)})


SAMPLE_DOCS: list[
    tuple[str, str, str, list[tuple[str, str]]]
] = [
    (
        "Product Launch Plan",
        "shiva@example.com",
        _doc(
            _h(1, "Product Launch Plan"),
            _p(
                _text("Goal: ship the beta to "),
                _text("50 pilot teams", "bold"),
                _text(" by the end of the quarter."),
            ),
            _h(2, "Milestones"),
            _list(
                "ol",
                "Finalize scope",
                "Internal dogfooding",
                "Pilot rollout",
                "Public announcement",
            ),
            _h(2, "Open questions"),
            _list(
                "ul",
                "Pricing for pilot teams",
                "Support rota during rollout",
            ),
            _p(
                _text("Owner: Shiva. ", "italic"),
                _text("Priya can edit; Sai can view.", "underline"),
            ),
        ),
        [
            ("priya@example.com", "editor"),
            ("sai@example.com", "viewer"),
        ],
    ),
    (
        "Kickoff Meeting Notes",
        "shiva@example.com",
        _doc(
            _h(2, "Kickoff — attendees: Shiva, Priya, Sai"),
            _p(_text("Decisions", "bold")),
            _list(
                "ul",
                "Weekly check-in on Tuesdays",
                "Design review before any build work",
            ),
            _p(_text("Action items", "bold")),
            _list(
                "ol",
                "Shiva: draft launch plan",
                "Priya: design review checklist",
                "Sai: set up CI",
            ),
        ),
        [],
    ),
    (
        "Design Review Checklist",
        "priya@example.com",
        _doc(
            _h(1, "Design Review Checklist"),
            _p(_text("Use this before sending a design for sign-off.")),
            _list(
                "ul",
                "Accessible colour contrast",
                "Keyboard navigation",
                "Empty and error states",
                "Mobile layout",
            ),
        ),
        [("shiva@example.com", "viewer")],
    ),
]


def migrate_demo_users(db: Session) -> None:
    """Rename existing demo accounts without changing their IDs or relationships."""
    existing_users = {
        user.email.lower(): user
        for user in db.query(User).all()
    }

    # Check every target address before changing anything.
    for old_email, new_data in DEMO_USER_MIGRATIONS.items():
        old_user = existing_users.get(old_email)
        target_user = existing_users.get(new_data["email"])

        if old_user and target_user and old_user.id != target_user.id:
            raise RuntimeError(
                f"Cannot migrate {old_email}: "
                f"{new_data['email']} is already used by another account."
            )

    changed = False

    for old_email, new_data in DEMO_USER_MIGRATIONS.items():
        user = existing_users.get(old_email)

        if user:
            user.name = new_data["name"]
            user.email = new_data["email"]
            changed = True

    if changed:
        db.commit()
        print("✓ Existing demo accounts migrated to Shiva, Priya, and Sai.")


def run_seed(db: Session) -> None:
    """Migrate existing demo identities or seed an empty database."""
    if db.query(User).count() > 0:
        migrate_demo_users(db)
        return

    users: dict[str, User] = {}

    for data in DEMO_USERS:
        user = User(
            name=data["name"],
            email=data["email"],
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        users[data["email"]] = user

    db.flush()

    for title, owner_email, content, shares in SAMPLE_DOCS:
        doc = Document(
            title=title,
            content=content,
            owner_id=users[owner_email].id,
        )
        db.add(doc)
        db.flush()

        for email, permission in shares:
            db.add(
                Share(
                    document_id=doc.id,
                    user_id=users[email].id,
                    permission=permission,
                )
            )

    db.commit()
    print("✓ Database seeded with Shiva, Priya, and Sai demo users.")


if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        run_seed(session)
