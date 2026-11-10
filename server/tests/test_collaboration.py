"""Behaviour the editor relies on: timestamps, save conflicts, permission changes."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Document, Share
from tests.conftest import create_test_user, get_auth_headers

DOC_JSON = '{"type": "doc", "content": []}'


def _setup(db: Session) -> tuple:
    owner = create_test_user(db, name="Owner", email="owner@example.com")
    editor = create_test_user(db, name="Editor", email="editor@example.com")
    doc = Document(title="Shared", owner_id=owner.id, content=DOC_JSON)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    share = Share(document_id=doc.id, user_id=editor.id, permission="editor")
    db.add(share)
    db.commit()
    db.refresh(share)
    return owner, editor, doc, share


class TestTimestamps:
    def test_timestamps_are_utc_with_offset(self, client: TestClient, db: Session) -> None:
        """Naive SQLite datetimes must be emitted with an explicit UTC offset."""
        owner, _, doc, _ = _setup(db)
        data = client.get(f"/api/documents/{doc.id}", headers=get_auth_headers(owner)).json()
        assert data["updated_at"].endswith(("Z", "+00:00"))
        assert data["created_at"].endswith(("Z", "+00:00"))


class TestSaveConflicts:
    def test_save_with_current_version_succeeds(self, client: TestClient, db: Session) -> None:
        owner, _, doc, _ = _setup(db)
        headers = get_auth_headers(owner)
        seen = client.get(f"/api/documents/{doc.id}", headers=headers).json()["updated_at"]

        r = client.put(
            f"/api/documents/{doc.id}",
            json={"title": "v2", "expected_updated_at": seen},
            headers=headers,
        )
        assert r.status_code == 200
        # The returned version can be used for the next save (auto-save chain).
        r2 = client.put(
            f"/api/documents/{doc.id}",
            json={"title": "v3", "expected_updated_at": r.json()["updated_at"]},
            headers=headers,
        )
        assert r2.status_code == 200

    def test_stale_save_is_rejected_not_overwritten(self, client: TestClient, db: Session) -> None:
        """Two people open the doc; the second save based on the old version gets 409."""
        owner, editor, doc, _ = _setup(db)
        owner_h, editor_h = get_auth_headers(owner), get_auth_headers(editor)
        opened_at = client.get(f"/api/documents/{doc.id}", headers=editor_h).json()["updated_at"]

        assert client.put(
            f"/api/documents/{doc.id}",
            json={"title": "Owner's edit", "expected_updated_at": opened_at},
            headers=owner_h,
        ).status_code == 200

        stale = client.put(
            f"/api/documents/{doc.id}",
            json={"title": "Editor's edit", "expected_updated_at": opened_at},
            headers=editor_h,
        )
        assert stale.status_code == 409
        assert client.get(f"/api/documents/{doc.id}", headers=owner_h).json()["title"] == "Owner's edit"

    def test_save_without_version_is_last_write_wins(self, client: TestClient, db: Session) -> None:
        owner, _, doc, _ = _setup(db)
        r = client.put(f"/api/documents/{doc.id}", json={"title": "forced"}, headers=get_auth_headers(owner))
        assert r.status_code == 200


class TestChangePermission:
    def test_owner_can_downgrade_editor_to_viewer(self, client: TestClient, db: Session) -> None:
        owner, editor, doc, share = _setup(db)
        r = client.patch(
            f"/api/documents/{doc.id}/shares/{share.id}",
            json={"permission": "viewer"},
            headers=get_auth_headers(owner),
        )
        assert r.status_code == 200
        assert r.json()["permission"] == "viewer"

        # The downgrade takes effect immediately.
        blocked = client.put(
            f"/api/documents/{doc.id}", json={"title": "nope"}, headers=get_auth_headers(editor)
        )
        assert blocked.status_code == 403

    def test_non_owner_cannot_change_permission(self, client: TestClient, db: Session) -> None:
        _, editor, doc, share = _setup(db)
        r = client.patch(
            f"/api/documents/{doc.id}/shares/{share.id}",
            json={"permission": "editor"},
            headers=get_auth_headers(editor),
        )
        assert r.status_code == 403
