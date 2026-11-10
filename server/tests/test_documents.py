from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Document, Share
from tests.conftest import create_test_user, get_auth_headers


class TestCreateDocument:
    """Tests for POST /api/documents."""

    def test_create_document(self, client: TestClient, db: Session) -> None:
        """A user can create a new document."""
        user = create_test_user(db)
        headers = get_auth_headers(user)
        response = client.post(
            "/api/documents",
            json={"title": "My Doc"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Doc"
        assert data["owner_id"] == user.id
        assert data["role"] == "owner"

    def test_create_document_with_content(self, client: TestClient, db: Session) -> None:
        """A user can create a document with initial content."""
        user = create_test_user(db)
        headers = get_auth_headers(user)
        content = json.dumps({"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}]})
        response = client.post(
            "/api/documents",
            json={"title": "With Content", "content": content},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == content


class TestGetDocument:
    """Tests for GET /api/documents/{id}."""

    def test_get_own_document(self, client: TestClient, db: Session) -> None:
        """An owner can retrieve their own document."""
        user = create_test_user(db)
        headers = get_auth_headers(user)
        doc = Document(title="Test", owner_id=user.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get(f"/api/documents/{doc.id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Test"
        assert response.json()["role"] == "owner"

    def test_get_document_not_found(self, client: TestClient, db: Session) -> None:
        """Requesting a non-existent document returns 404."""
        user = create_test_user(db)
        headers = get_auth_headers(user)
        response = client.get("/api/documents/nonexistent-id", headers=headers)
        assert response.status_code == 404

    def test_get_document_forbidden(self, client: TestClient, db: Session) -> None:
        """A user without access gets 403."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        other = create_test_user(db, email="other@example.com", name="Other")
        doc = Document(title="Private", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        headers = get_auth_headers(other)
        response = client.get(f"/api/documents/{doc.id}", headers=headers)
        assert response.status_code == 403


class TestUpdateDocument:
    """Tests for PUT /api/documents/{id}."""

    def test_owner_can_update(self, client: TestClient, db: Session) -> None:
        """The owner can update title and content."""
        user = create_test_user(db)
        headers = get_auth_headers(user)
        doc = Document(title="Old Title", owner_id=user.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.put(
            f"/api/documents/{doc.id}",
            json={"title": "New Title"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"

    def test_viewer_cannot_update(self, client: TestClient, db: Session) -> None:
        """A viewer cannot update a document."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        viewer = create_test_user(db, email="viewer@example.com", name="Viewer")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=viewer.id, permission="viewer")
        db.add(share)
        db.commit()

        headers = get_auth_headers(viewer)
        response = client.put(
            f"/api/documents/{doc.id}",
            json={"title": "Hacked"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_editor_can_update(self, client: TestClient, db: Session) -> None:
        """An editor can update a document."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        editor = create_test_user(db, email="editor@example.com", name="Editor")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=editor.id, permission="editor")
        db.add(share)
        db.commit()

        headers = get_auth_headers(editor)
        response = client.put(
            f"/api/documents/{doc.id}",
            json={"title": "Updated by Editor"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated by Editor"


class TestDeleteDocument:
    """Tests for DELETE /api/documents/{id}."""

    def test_owner_can_delete(self, client: TestClient, db: Session) -> None:
        """The owner can delete their document."""
        user = create_test_user(db)
        headers = get_auth_headers(user)
        doc = Document(title="To Delete", owner_id=user.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.delete(f"/api/documents/{doc.id}", headers=headers)
        assert response.status_code == 204

    def test_non_owner_cannot_delete(self, client: TestClient, db: Session) -> None:
        """A non-owner cannot delete a document."""
        owner = create_test_user(db, email="owner@example.com", name="Owner")
        editor = create_test_user(db, email="editor@example.com", name="Editor")
        doc = Document(title="Doc", owner_id=owner.id, content="{}")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = Share(document_id=doc.id, user_id=editor.id, permission="editor")
        db.add(share)
        db.commit()

        headers = get_auth_headers(editor)
        response = client.delete(f"/api/documents/{doc.id}", headers=headers)
        assert response.status_code == 403


class TestListDocuments:
    """Tests for GET /api/documents."""

    def test_list_owned_and_shared(self, client: TestClient, db: Session) -> None:
        """Listing documents returns both owned and shared docs with correct roles."""
        alice = create_test_user(db, email="alice@example.com", name="Alice")
        bob = create_test_user(db, email="bob@example.com", name="Bob")

        # Alice creates a doc
        doc1 = Document(title="Alice Doc", owner_id=alice.id, content="{}")
        db.add(doc1)

        # Bob creates a doc
        doc2 = Document(title="Bob Doc", owner_id=bob.id, content="{}")
        db.add(doc2)
        db.commit()
        db.refresh(doc1)
        db.refresh(doc2)

        # Share Bob's doc with Alice as viewer
        share = Share(document_id=doc2.id, user_id=alice.id, permission="viewer")
        db.add(share)
        db.commit()

        headers = get_auth_headers(alice)
        response = client.get("/api/documents", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        titles = {d["title"]: d["role"] for d in data}
        assert titles["Alice Doc"] == "owner"
        assert titles["Bob Doc"] == "viewer"
