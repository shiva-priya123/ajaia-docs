from __future__ import annotations

from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.utils.time import UTCDateTime


class ShareCreate(BaseModel):
    """Request body for creating a share."""
    user_id: str = Field(min_length=1, max_length=36)
    permission: Literal["viewer", "editor"]


class ShareUpdate(BaseModel):
    """Request body for changing an existing share's permission."""
    permission: Literal["viewer", "editor"]


class ShareOut(BaseModel):
    """Response body for a share entry."""
    id: str
    document_id: str
    user_id: str
    user_name: str
    user_email: str
    permission: Literal["viewer", "editor"]
    created_at: UTCDateTime

    model_config = ConfigDict(from_attributes=True)
