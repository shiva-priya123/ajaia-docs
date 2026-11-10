from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import create_test_user, get_auth_headers


class TestLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client: TestClient, db: Session) -> None:
        """A valid email/password pair returns a token and user info."""
        user = create_test_user(db, email="alice@example.com", name="Alice")
        response = client.post(
            "/api/auth/login",
            json={"email": "alice@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["name"] == "Alice"
        assert data["user"]["id"] == user.id

    def test_login_wrong_password(self, client: TestClient, db: Session) -> None:
        """An incorrect password returns 401."""
        create_test_user(db, email="alice@example.com")
        response = client.post(
            "/api/auth/login",
            json={"email": "alice@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient, db: Session) -> None:
        """A non-existent email returns 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert response.status_code == 401


class TestGetMe:
    """Tests for GET /api/auth/me."""

    def test_get_me_authenticated(self, client: TestClient, db: Session) -> None:
        """An authenticated user can retrieve their own profile."""
        user = create_test_user(db, name="Alice", email="alice@example.com")
        headers = get_auth_headers(user)
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "alice@example.com"
        assert data["name"] == "Alice"

    def test_get_me_unauthenticated(self, client: TestClient) -> None:
        """A request without a token returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
