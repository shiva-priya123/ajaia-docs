from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Document, Share
from tests.conftest import create_test_user, get_auth_headers


class TestShareCreation:
    """Tests for POST /api/documents/{id}/shares."""

    def test_owner_can_share(self, client: TestClient, db: Session) -> None:
        """The document owner can share it with another user."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        target = create_test_user(db, email="target@example.com", name="Target")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        headers = get_auth_headers(owner)
        response = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"user_id": target.id, "permission": "editor"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == target.id
        assert data["permission"] == "editor"
        assert data["user_name"] == "Target"

    def test_non_owner_cannot_share(self, client: TestClient, db: Session) -> None:
        """A non-owner cannot share a document."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        other = create_test_user(db, email="other@example.com", name="Other")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        headers = get_auth_headers(other)
        response = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"user_id": owner.id, "permission": "viewer"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_cannot_share_with_self(self, client: TestClient, db: Session) -> None:
        """The owner cannot share a document with themselves."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        headers = get_auth_headers(owner)
        response = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"user_id": owner.id, "permission": "editor"},
            headers=headers,
        )
        assert response.status_code == 400

    def test_duplicate_share_rejected(self, client: TestClient, db: Session) -> None:
        """Sharing with the same user twice is rejected."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        target = create_test_user(db, email="target@example.com", name="Target")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=target.id, permission="viewer")
        db.add(share)
        db.commit()

        headers = get_auth_headers(owner)
        response = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"user_id": target.id, "permission": "editor"},
            headers=headers,
        )
        assert response.status_code == 400


class TestShareListing:
    """Tests for GET /api/documents/{id}/shares."""

    def test_owner_can_list_shares(self, client: TestClient, db: Session) -> None:
        """The owner can list all shares for their document."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        target = create_test_user(db, email="target@example.com", name="Target")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=target.id, permission="editor")
        db.add(share)
        db.commit()

        headers = get_auth_headers(owner)
        response = client.get(f"/api/documents/{doc.id}/shares", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_name"] == "Target"
        assert data[0]["permission"] == "editor"


class TestShareDeletion:
    """Tests for DELETE /api/documents/{id}/shares/{share_id}."""

    def test_owner_can_remove_share(self, client: TestClient, db: Session) -> None:
        """The owner can remove a share."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        target = create_test_user(db, email="target@example.com", name="Target")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=target.id, permission="editor")
        db.add(share)
        db.commit()
        db.refresh(share)

        headers = get_auth_headers(owner)
        response = client.delete(
            f"/api/documents/{doc.id}/shares/{share.id}",
            headers=headers,
        )
        assert response.status_code == 204

    def test_non_owner_cannot_remove_share(self, client: TestClient, db: Session) -> None:
        """A non-owner cannot remove a share."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        target = create_test_user(db, email="target@example.com", name="Target")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=target.id, permission="editor")
        db.add(share)
        db.commit()
        db.refresh(share)

        headers = get_auth_headers(target)
        response = client.delete(
            f"/api/documents/{doc.id}/shares/{share.id}",
            headers=headers,
        )
        assert response.status_code == 403
