from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

# Must run before `app` is imported: the app's lifespan creates tables and seeds
# demo data on whatever DATABASE_URL points to. Point it at a throwaway file so
# running the tests never touches the developer's ajaia_docs.db.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp(prefix='ajaia-test-')}/app.db"
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.auth.service import create_access_token, hash_password
from app.database import Base, get_db
from app.main import application
from app.models import User


# In-memory SQLite for tests
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, Any, None]:
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db() -> Generator[Session, Any, None]:
    """Yield a test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """Create a FastAPI TestClient with the test DB override."""

    def _override_get_db() -> Generator[Session, Any, None]:
        yield db

    application.dependency_overrides[get_db] = _override_get_db
    with TestClient(application, raise_server_exceptions=False) as c:
        yield c
    application.dependency_overrides.clear()


def create_test_user(
    db: Session,
    *,
    name: str = "Test User",
    email: str = "test@example.com",
    password: str = "password123",
) -> User:
    """Create and persist a test user, returning the ORM object."""
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user: User) -> dict[str, str]:
    """Generate an Authorization header dict for the given user."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}
