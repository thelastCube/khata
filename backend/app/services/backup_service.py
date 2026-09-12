"""Export every table to CSV under data/exports/. If that directory is
inside a git repo, the caller can commit/push it; wiring the auto-push
is a deploy-time concern (see plan.md)."""
import csv
import sqlite3
from pathlib import Path

from ..config import get_settings

TABLES = [
    "funds", "budgets", "expenses", "labels", "expense_labels",
    "label_groups", "group_labels", "transfers", "carry_adjustments", "audit_log",
]


class BackupService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def export_csv(self, out_dir: Path | None = None) -> dict:
        base = Path(out_dir or (get_settings().db_path.parent / "exports"))
        base.mkdir(parents=True, exist_ok=True)
        written = {}
        for table in TABLES:
            rows = self.conn.execute(f"SELECT * FROM {table}").fetchall()
            path = base / f"{table}.csv"
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                if rows:
                    writer.writerow(rows[0].keys())
                    writer.writerows([tuple(r) for r in rows])
                else:
                    cols = [c[1] for c in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    writer.writerow(cols)
            written[table] = len(rows)
        return {"dir": str(base), "rows": written}
