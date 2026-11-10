from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    """Public user representation for the users list endpoint."""
    id: str
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)
