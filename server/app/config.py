from __future__ import annotations

from pydantic_settings import BaseSettings

DEFAULT_JWT_SECRET = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    JWT_SECRET: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    DATABASE_URL: str = "sqlite:///./ajaia_docs.db"

    # Comma-separated list of origins allowed to call the API cross-origin.
    # Only needed in local dev (Vite on :5173); in production the API serves the
    # built frontend from the same origin.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024  # 5 MB
    MAX_CONTENT_BYTES: int = 2 * 1024 * 1024  # 2 MB of TipTap JSON per document

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
