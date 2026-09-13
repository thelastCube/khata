"""The central auth database: profiles (users) live here, separate from each
profile's own data DB. One file: data/auth.db."""
import sqlite3
from pathlib import Path

from fastapi import Depends

from .config import Settings, get_settings

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL UNIQUE COLLATE NOCASE,
    avatar               TEXT,                       -- emoji, or a data: URI
    password_hash        TEXT NOT NULL,
    is_admin             INTEGER NOT NULL DEFAULT 0,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT NOT NULL
);
"""


def auth_db_path(settings: Settings) -> Path:
    return settings.data_dir / "auth.db"


def connect_auth(settings: Settings) -> sqlite3.Connection:
    path = auth_db_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_auth_db(settings: Settings) -> None:
    conn = connect_auth(settings)
    try:
        conn.executescript(AUTH_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_auth_db(settings: Settings = Depends(get_settings)):
    """FastAPI dependency: one auth-DB connection per request."""
    conn = connect_auth(settings)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
