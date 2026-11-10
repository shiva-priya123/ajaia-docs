from __future__ import annotations

from fastapi import HTTPException, status


def not_found(detail: str = "Resource not found") -> HTTPException:
    """Return a 404 Not Found exception."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def forbidden(detail: str = "You do not have permission to perform this action") -> HTTPException:
    """Return a 403 Forbidden exception."""
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def bad_request(detail: str = "Bad request") -> HTTPException:
    """Return a 400 Bad Request exception."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def unauthorized(detail: str = "Invalid credentials") -> HTTPException:
    """Return a 401 Unauthorized exception."""
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def payload_too_large(detail: str = "Payload too large") -> HTTPException:
    """Return a 413 Payload Too Large exception."""
    return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)


def conflict(detail: str = "Conflict") -> HTTPException:
    """Return a 409 Conflict exception."""
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
