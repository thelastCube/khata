"""SQL for siphon transfers between funds."""
import sqlite3

from ..models import Transfer


class TransfersDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _row(r: sqlite3.Row) -> Transfer:
        return Transfer(
            id=r["id"], month=r["month"], from_fund_id=r["from_fund_id"], to_fund_id=r["to_fund_id"],
            amount=r["amount"], reason=r["reason"], trigger_expense_id=r["trigger_expense_id"], ts=r["ts"],
        )

    def create(self, t: Transfer) -> Transfer:
        cur = self.conn.execute(
            """INSERT INTO transfers(month, from_fund_id, to_fund_id, amount, reason, trigger_expense_id, ts)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (t.month, t.from_fund_id, t.to_fund_id, t.amount, t.reason, t.trigger_expense_id, t.ts),
        )
        t.id = cur.lastrowid
        return t

    def list_for_month(self, month: str) -> list[Transfer]:
        rows = self.conn.execute(
            "SELECT * FROM transfers WHERE month = ? ORDER BY ts DESC, id DESC", (month,)
        ).fetchall()
        return [self._row(r) for r in rows]

    def list_for_fund(self, fund_id: int, month: str) -> list[Transfer]:
        rows = self.conn.execute(
            "SELECT * FROM transfers WHERE month = ? AND (from_fund_id = ? OR to_fund_id = ?) ORDER BY ts DESC",
            (month, fund_id, fund_id),
        ).fetchall()
        return [self._row(r) for r in rows]

    def sum_in(self, fund_id: int, month: str) -> float:
        r = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM transfers WHERE to_fund_id = ? AND month = ?",
            (fund_id, month),
        ).fetchone()
        return float(r["s"])

    def sum_out(self, fund_id: int, month: str) -> float:
        r = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM transfers WHERE from_fund_id = ? AND month = ?",
            (fund_id, month),
        ).fetchone()
        return float(r["s"])
