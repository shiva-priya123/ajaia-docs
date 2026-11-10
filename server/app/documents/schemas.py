from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

from app.config import settings
from app.utils.time import UTCDateTime

TITLE_MAX_LENGTH = 255

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_MAX_LENGTH)]


def validate_tiptap_content(value: Optional[str]) -> Optional[str]:
    """Content is a TipTap document serialised as JSON: {"type": "doc", ...}."""
    if value is None:
        return value
    if len(value.encode("utf-8")) > settings.MAX_CONTENT_BYTES:
        raise ValueError(
            f"Document is too large (max {settings.MAX_CONTENT_BYTES // (1024 * 1024)} MB)."
        )
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("Content must be valid JSON.") from exc
    if not isinstance(parsed, dict) or parsed.get("type") != "doc":
        raise ValueError('Content must be a TipTap document (an object with "type": "doc").')
    if "content" in parsed and not isinstance(parsed["content"], list):
        raise ValueError('"content" must be a list of nodes.')
    return value


class DocumentCreate(BaseModel):
    """Request body for creating a new document."""
    title: Title = "Untitled"
    content: Optional[str] = None

    @field_validator("content")
    @classmethod
    def _check_content(cls, value: Optional[str]) -> Optional[str]:
        return validate_tiptap_content(value)


class DocumentUpdate(BaseModel):
    """Request body for updating an existing document (partial update)."""
    title: Optional[Title] = None
    content: Optional[str] = None
    # Optimistic concurrency: the `updated_at` the client last saw. If the
    # document changed since then (another editor saved), the update is
    # rejected with 409 instead of silently overwriting their work.
    expected_updated_at: Optional[datetime] = None

    @field_validator("content")
    @classmethod
    def _check_content(cls, value: Optional[str]) -> Optional[str]:
        return validate_tiptap_content(value)

    @model_validator(mode="after")
    def _require_a_field(self) -> "DocumentUpdate":
        if self.title is None and self.content is None:
            raise ValueError("Provide a title and/or content to update.")
        return self


class DocumentOut(BaseModel):
    """Response body for a document."""
    id: str
    title: str
    content: Optional[str] = None
    owner_id: str
    owner_name: str
    role: Literal["owner", "editor", "viewer"]
    created_at: UTCDateTime
    updated_at: UTCDateTime

    model_config = ConfigDict(from_attributes=True)
