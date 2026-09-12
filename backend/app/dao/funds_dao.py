"""SQL for funds. Name matching is case-insensitive (COLLATE NOCASE);
the stored name keeps its original case."""
import sqlite3

from ..models import Fund


class FundsDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _row(r: sqlite3.Row) -> Fund:
        return Fund(
            id=r["id"], name=r["name"], color=r["color"], sort=r["sort"], active=bool(r["active"]),
            default_amount=r["default_amount"],
            default_carry_underspend=bool(r["default_carry_underspend"]),
            default_carry_overspend=bool(r["default_carry_overspend"]),
            default_emi_months=r["default_emi_months"],
        )

    def create(self, f: Fund) -> Fund:
        cur = self.conn.execute(
            """INSERT INTO funds(name, color, sort, active, default_amount,
                                 default_carry_underspend, default_carry_overspend, default_emi_months)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (f.name, f.color, f.sort, int(f.active), f.default_amount,
             int(f.default_carry_underspend), int(f.default_carry_overspend), f.default_emi_months),
        )
        f.id = cur.lastrowid
        return f

    def get(self, fund_id: int) -> Fund | None:
        r = self.conn.execute("SELECT * FROM funds WHERE id = ?", (fund_id,)).fetchone()
        return self._row(r) if r else None

    def get_by_name(self, name: str) -> Fund | None:
        r = self.conn.execute("SELECT * FROM funds WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return self._row(r) if r else None

    def list(self, include_inactive: bool = False) -> list[Fund]:
        q = "SELECT * FROM funds"
        if not include_inactive:
            q += " WHERE active = 1"
        q += " ORDER BY sort, name"
        return [self._row(r) for r in self.conn.execute(q).fetchall()]

    def update(self, f: Fund) -> Fund:
        self.conn.execute(
            """UPDATE funds SET name = ?, color = ?, sort = ?, active = ?, default_amount = ?,
                   default_carry_underspend = ?, default_carry_overspend = ?, default_emi_months = ?
               WHERE id = ?""",
            (f.name, f.color, f.sort, int(f.active), f.default_amount,
             int(f.default_carry_underspend), int(f.default_carry_overspend), f.default_emi_months, f.id),
        )
        return f

    def delete(self, fund_id: int) -> None:
        self.conn.execute("DELETE FROM funds WHERE id = ?", (fund_id,))
