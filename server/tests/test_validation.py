"""Request validation: bad input gets a 4xx with a clear message, never a 500."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Document
from tests.conftest import create_test_user, get_auth_headers


def _make_doc(db: Session, owner_id: str) -> Document:
    doc = Document(title="Doc", owner_id=owner_id, content='{"type": "doc", "content": []}')
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class TestDocumentValidation:
    def test_create_defaults_title_to_untitled(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        response = client.post("/api/documents", json={}, headers=get_auth_headers(user))
        assert response.status_code == 201
        assert response.json()["title"] == "Untitled"

    def test_blank_title_rejected(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        response = client.post("/api/documents", json={"title": "   "}, headers=get_auth_headers(user))
        assert response.status_code == 422

    def test_title_is_trimmed(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        response = client.post("/api/documents", json={"title": "  Plan  "}, headers=get_auth_headers(user))
        assert response.json()["title"] == "Plan"

    def test_overlong_title_rejected(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        response = client.post("/api/documents", json={"title": "x" * 256}, headers=get_auth_headers(user))
        assert response.status_code == 422

    def test_invalid_json_content_rejected(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        doc = _make_doc(db, user.id)
        response = client.put(
            f"/api/documents/{doc.id}", json={"content": "{not json"}, headers=get_auth_headers(user)
        )
        assert response.status_code == 422
        assert "valid JSON" in response.text

    def test_non_tiptap_content_rejected(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        doc = _make_doc(db, user.id)
        response = client.put(
            f"/api/documents/{doc.id}", json={"content": '{"hello": "world"}'}, headers=get_auth_headers(user)
        )
        assert response.status_code == 422

    def test_empty_update_rejected(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        doc = _make_doc(db, user.id)
        response = client.put(f"/api/documents/{doc.id}", json={}, headers=get_auth_headers(user))
        assert response.status_code == 422


class TestShareValidation:
    def test_invalid_permission_rejected(self, client: TestClient, db: Session) -> None:
        owner = create_test_user(db, email="owner@example.com")
        target = create_test_user(db, email="target@example.com")
        doc = _make_doc(db, owner.id)
        response = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"user_id": target.id, "permission": "admin"},
            headers=get_auth_headers(owner),
        )
        assert response.status_code == 422


class TestAuthValidation:
    def test_login_email_is_case_insensitive(self, client: TestClient, db: Session) -> None:
        create_test_user(db, email="alice@example.com", password="password123")
        response = client.post(
            "/api/auth/login", json={"email": "  Alice@Example.com ", "password": "password123"}
        )
        assert response.status_code == 200

    def test_invalid_token_rejected(self, client: TestClient) -> None:
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401
