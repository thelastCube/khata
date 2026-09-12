"""Application settings, loaded from environment / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Single-user auth.
    app_password: str = "changeme"
    secret_key: str = "dev-insecure-change-me"

    # Storage. One SQLite file; parent dir is created on connect.
    db_path: Path = BASE_DIR / "data" / "khata.db"

    # Session cookie.
    cookie_name: str = "budget_session"
    session_max_age: int = 60 * 60 * 24 * 30  # 30 days

    # Frontend dev origins (Vite default).
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
