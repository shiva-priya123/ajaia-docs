from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Request body for the login endpoint."""
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public user representation returned in auth responses."""
    id: str
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Response body for successful login."""
    token: str
    user: UserResponse
