"""The demo seed must show every sharing state and be safe to run repeatedly."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import Document, Share, User
from app.seed import run_seed


def test_seed_covers_owned_and_shared_documents(db: Session) -> None:
    run_seed(db)
    users = {u.email: u for u in db.query(User).all()}
    assert set(users) == {"alice@example.com", "bob@example.com", "charlie@example.com"}

    permissions = {(s.user.email, s.permission) for s in db.query(Share).all()}
    # Each demo user has something shared with them, covering both permission levels.
    assert ("bob@example.com", "editor") in permissions
    assert ("charlie@example.com", "viewer") in permissions
    assert ("alice@example.com", "viewer") in permissions

    for doc in db.query(Document).all():
        assert json.loads(doc.content)["type"] == "doc"


def test_seed_is_idempotent(db: Session) -> None:
    run_seed(db)
    run_seed(db)
    assert db.query(User).count() == 3
    assert db.query(Document).count() == 3


def test_seeded_user_can_log_in(client, db: Session) -> None:
    run_seed(db)
    r = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "password123"})
    assert r.status_code == 200
    docs = client.get("/api/documents", headers={"Authorization": f"Bearer {r.json()['token']}"}).json()
    roles = {d["title"]: d["role"] for d in docs}
    assert roles == {"Design Review Checklist": "owner", "Product Launch Plan": "editor"}
