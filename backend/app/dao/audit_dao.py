"""SQL for the human-readable audit log."""
import json
import sqlite3

from ..util import now_iso


class AuditDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def log(self, action: str, entity: str | None = None,
            entity_id: int | None = None, detail: dict | None = None) -> None:
        self.conn.execute(
            "INSERT INTO audit_log(ts, action, entity, entity_id, detail_json) VALUES (?, ?, ?, ?, ?)",
            (now_iso(), action, entity, entity_id, json.dumps(detail) if detail is not None else None),
        )

    def list(self, entity: str | None = None, month: str | None = None, limit: int = 200) -> list[dict]:
        clauses, params = [], []
        if entity:
            clauses.append("entity = ?")
            params.append(entity)
        if month:
            clauses.append("substr(ts, 1, 7) = ?")
            params.append(month)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.conn.execute(
            f"SELECT * FROM audit_log{where} ORDER BY id DESC LIMIT ?", (*params, limit)
        ).fetchall()
        return [
            {
                "id": r["id"], "ts": r["ts"], "action": r["action"], "entity": r["entity"],
                "entity_id": r["entity_id"],
                "detail": json.loads(r["detail_json"]) if r["detail_json"] else None,
            }
            for r in rows
        ]
