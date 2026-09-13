"""SQLite connection + schema. The only module that defines the schema;
DAOs are the only modules that run queries against these tables."""
import sqlite3
from pathlib import Path

from fastapi import Depends

from .auth import current_user
from .config import Settings, get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS funds (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL UNIQUE,
    color  TEXT,
    sort   INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    -- default monthly budget; a row in `budgets` overrides it for that month
    default_amount           REAL    NOT NULL DEFAULT 0,
    default_carry_underspend INTEGER NOT NULL DEFAULT 0,
    default_carry_overspend  INTEGER NOT NULL DEFAULT 0,
    default_emi_months       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS budgets (
    fund_id          INTEGER NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    month            TEXT    NOT NULL,            -- YYYY-MM
    amount           REAL    NOT NULL DEFAULT 0,
    carry_underspend INTEGER NOT NULL DEFAULT 0,  -- roll leftover into next month
    carry_overspend  INTEGER NOT NULL DEFAULT 0,  -- shrink next month by overage
    emi_months       INTEGER NOT NULL DEFAULT 1,  -- spread overspend repayment
    PRIMARY KEY (fund_id, month)
);

CREATE TABLE IF NOT EXISTS expenses (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT    NOT NULL,                     -- ISO8601
    amount  REAL    NOT NULL,
    fund_id INTEGER NOT NULL REFERENCES funds(id),
    note    TEXT
);
CREATE INDEX IF NOT EXISTS idx_expenses_fund ON expenses(fund_id);
CREATE INDEX IF NOT EXISTS idx_expenses_ts   ON expenses(ts);

CREATE TABLE IF NOT EXISTS labels (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE,
    color TEXT
);

CREATE TABLE IF NOT EXISTS expense_labels (
    expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    label_id   INTEGER NOT NULL REFERENCES labels(id)   ON DELETE CASCADE,
    PRIMARY KEY (expense_id, label_id)
);

CREATE TABLE IF NOT EXISTS label_groups (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS group_labels (
    group_id INTEGER NOT NULL REFERENCES label_groups(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id)       ON DELETE CASCADE,
    PRIMARY KEY (group_id, label_id)
);

CREATE TABLE IF NOT EXISTS transfers (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    month              TEXT    NOT NULL,
    from_fund_id       INTEGER NOT NULL REFERENCES funds(id),
    to_fund_id         INTEGER NOT NULL REFERENCES funds(id),
    amount             REAL    NOT NULL,
    reason             TEXT,
    trigger_expense_id INTEGER REFERENCES expenses(id) ON DELETE SET NULL,
    ts                 TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS carry_adjustments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_id       INTEGER NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    month         TEXT    NOT NULL,     -- month this adjustment applies to
    amount        REAL    NOT NULL,     -- +roll-in / -repayment
    source_month  TEXT,                 -- month it originated from
    kind          TEXT    NOT NULL,     -- 'underspend_rollin' | 'overspend_repay'
    emi_remaining INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_carry_fund_month ON carry_adjustments(fund_id, month);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    action      TEXT NOT NULL,
    entity      TEXT,
    entity_id   INTEGER,
    detail_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or get_settings().db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def profile_db_path(settings: Settings, user_id: int) -> Path:
    return settings.data_dir / "profiles" / f"{user_id}.db"


def get_db(user=Depends(current_user), settings: Settings = Depends(get_settings)):
    """FastAPI dependency: one connection per request = one transaction, scoped
    to the logged-in profile's own SQLite file. Commit on success, rollback on
    any error. DAOs run statements and services hold logic — neither commits.

    This is the single seam that isolates every profile's data: the connection
    always points at the current user's file, so no route can reach another
    profile's data."""
    path = profile_db_path(settings, user.id)
    if not path.exists():
        init_db(path)
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
