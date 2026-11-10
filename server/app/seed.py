"""Seed the database with demo users and sample documents.

Runs automatically on startup when the database has no users, and can be run
standalone: ``python -m app.seed``.

The data is chosen so every demo account immediately shows both sides of the
sharing model: documents they own, and documents shared with them as a viewer
or an editor.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.auth.service import hash_password
from app.models import Document, Share, User

DEMO_PASSWORD = "password123"
DEMO_USERS = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"},
]


# ── Tiny TipTap JSON builders (keeps the sample docs readable) ───────────────
def _text(text: str, *marks: str) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    if marks:
        node["marks"] = [{"type": m} for m in marks]
    return node


def _p(*content: dict[str, Any]) -> dict[str, Any]:
    return {"type": "paragraph", "content": list(content)}


def _h(level: int, text: str) -> dict[str, Any]:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(text)]}


def _list(kind: str, *items: str) -> dict[str, Any]:
    return {
        "type": "bulletList" if kind == "ul" else "orderedList",
        "content": [{"type": "listItem", "content": [_p(_text(i))]} for i in items],
    }


def _doc(*blocks: dict[str, Any]) -> str:
    return json.dumps({"type": "doc", "content": list(blocks)})


# (title, owner email, content, [(shared-with email, permission), ...])
SAMPLE_DOCS: list[tuple[str, str, str, list[tuple[str, str]]]] = [
    (
        "Product Launch Plan",
        "alice@example.com",
        _doc(
            _h(1, "Product Launch Plan"),
            _p(_text("Goal: ship the beta to "), _text("50 pilot teams", "bold"), _text(" by the end of the quarter.")),
            _h(2, "Milestones"),
            _list("ol", "Finalize scope", "Internal dogfooding", "Pilot rollout", "Public announcement"),
            _h(2, "Open questions"),
            _list("ul", "Pricing for pilot teams", "Support rota during rollout"),
            _p(_text("Owner: Alice. ", "italic"), _text("Bob can edit; Charlie can view.", "underline")),
        ),
        [("bob@example.com", "editor"), ("charlie@example.com", "viewer")],
    ),
    (
        "Kickoff Meeting Notes",
        "alice@example.com",
        _doc(
            _h(2, "Kickoff — attendees: Alice, Bob, Charlie"),
            _p(_text("Decisions", "bold")),
            _list("ul", "Weekly check-in on Tuesdays", "Design review before any build work"),
            _p(_text("Action items", "bold")),
            _list("ol", "Alice: draft launch plan", "Bob: design review checklist", "Charlie: set up CI"),
        ),
        [],
    ),
    (
        "Design Review Checklist",
        "bob@example.com",
        _doc(
            _h(1, "Design Review Checklist"),
            _p(_text("Use this before sending a design for sign-off.")),
            _list("ul", "Accessible colour contrast", "Keyboard navigation", "Empty and error states", "Mobile layout"),
        ),
        [("alice@example.com", "viewer")],
    ),
]


def run_seed(db: Session) -> None:
    """Insert demo data if the database is empty (idempotent)."""
    if db.query(User).count() > 0:
        return

    users: dict[str, User] = {}
    for data in DEMO_USERS:
        user = User(name=data["name"], email=data["email"], password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        users[data["email"]] = user
    db.flush()  # populate ids

    for title, owner_email, content, shares in SAMPLE_DOCS:
        doc = Document(title=title, content=content, owner_id=users[owner_email].id)
        db.add(doc)
        db.flush()
        for email, permission in shares:
            db.add(Share(document_id=doc.id, user_id=users[email].id, permission=permission))

    db.commit()
    print("✓ Database seeded with demo users and sample documents.")


if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        run_seed(session)
