from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def as_utc(value: datetime) -> datetime:
    """SQLite drops tzinfo on read; all stored times are UTC, so re-attach it.

    Without this the API would emit "2026-01-01T12:00:00" (no offset) and
    browsers would parse it as *local* time.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# Use for every datetime field in API responses.
UTCDateTime = Annotated[datetime, AfterValidator(as_utc)]
