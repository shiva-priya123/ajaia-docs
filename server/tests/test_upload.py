from __future__ import annotations

import io
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import create_test_user, get_auth_headers


class TestUpload:
    """Tests for POST /api/upload."""

    def test_upload_txt_file(self, client: TestClient, db: Session) -> None:
        """Uploading a .txt file creates a new document."""
        user = create_test_user(db)
        headers = get_auth_headers(user)

        content = b"Hello World\nThis is line two."
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "test"
        assert "document_id" in data
        assert "Successfully imported" in data["message"]

    def test_upload_unsupported_type(self, client: TestClient, db: Session) -> None:
        """Uploading an unsupported file type returns 400."""
        user = create_test_user(db)
        headers = get_auth_headers(user)

        content = b"some binary data"
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(content), "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 400

    def test_upload_md_file(self, client: TestClient, db: Session) -> None:
        """Uploading a .md file creates a new document with converted content."""
        user = create_test_user(db)
        headers = get_auth_headers(user)

        content = b"# Heading\n\nSome paragraph text."
        response = client.post(
            "/api/upload",
            files={"file": ("notes.md", io.BytesIO(content), "text/markdown")},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "notes"
        assert "document_id" in data

    def test_upload_docx_preserves_formatting(self, client: TestClient, db: Session) -> None:
        """A .docx import becomes a document whose stored JSON keeps headings and marks."""
        from docx import Document as DocxDocument

        user = create_test_user(db)
        headers = get_auth_headers(user)

        d = DocxDocument()
        d.add_heading("Imported Heading", level=1)
        d.add_paragraph("").add_run("Bold text").bold = True
        buf = io.BytesIO()
        d.save(buf)

        response = client.post(
            "/api/upload",
            files={"file": ("report.docx", io.BytesIO(buf.getvalue()),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers,
        )
        assert response.status_code == 201
        doc_id = response.json()["document_id"]

        doc = client.get(f"/api/documents/{doc_id}", headers=headers).json()
        content = json.loads(doc["content"])
        assert content["content"][0]["type"] == "heading"
        assert content["content"][1]["content"][0]["marks"] == [{"type": "bold"}]

    def test_upload_empty_file(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        response = client.post(
            "/api/upload",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_too_large(self, client: TestClient, db: Session, monkeypatch) -> None:
        from app.config import settings

        monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 10)
        user = create_test_user(db)
        response = client.post(
            "/api/upload",
            files={"file": ("big.txt", io.BytesIO(b"x" * 11), "text/plain")},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 413

    def test_upload_corrupt_docx_returns_400_not_500(self, client: TestClient, db: Session) -> None:
        user = create_test_user(db)
        response = client.post(
            "/api/upload",
            files={"file": ("broken.docx", io.BytesIO(b"not a zip"), "application/octet-stream")},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 400
        assert "docx" in response.json()["detail"].lower()

    def test_upload_requires_auth(self, client: TestClient) -> None:
        response = client.post(
            "/api/upload", files={"file": ("a.txt", io.BytesIO(b"hi"), "text/plain")}
        )
        assert response.status_code == 401

    def test_raw_uploads_are_not_publicly_served(self, client: TestClient) -> None:
        """Raw files are not stored or exposed; /uploads must not be a public route."""
        assert client.get("/uploads/anything.txt").status_code == 404
