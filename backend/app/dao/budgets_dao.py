"""SQL for per-month budgets and carry adjustments."""
import sqlite3

from ..models import Budget, CarryAdjustment


class BudgetsDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _budget(r: sqlite3.Row) -> Budget:
        return Budget(
            fund_id=r["fund_id"],
            month=r["month"],
            amount=r["amount"],
            carry_underspend=bool(r["carry_underspend"]),
            carry_overspend=bool(r["carry_overspend"]),
            emi_months=r["emi_months"],
        )

    def get_budget(self, fund_id: int, month: str) -> Budget | None:
        r = self.conn.execute(
            "SELECT * FROM budgets WHERE fund_id = ? AND month = ?", (fund_id, month)
        ).fetchone()
        return self._budget(r) if r else None

    def upsert_budget(self, b: Budget) -> Budget:
        self.conn.execute(
            """INSERT INTO budgets(fund_id, month, amount, carry_underspend, carry_overspend, emi_months)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(fund_id, month) DO UPDATE SET
                 amount = excluded.amount,
                 carry_underspend = excluded.carry_underspend,
                 carry_overspend = excluded.carry_overspend,
                 emi_months = excluded.emi_months""",
            (b.fund_id, b.month, b.amount, int(b.carry_underspend), int(b.carry_overspend), b.emi_months),
        )
        return b

    def list_budgets(self, month: str) -> dict[int, Budget]:
        rows = self.conn.execute("SELECT * FROM budgets WHERE month = ?", (month,)).fetchall()
        return {r["fund_id"]: self._budget(r) for r in rows}

    def delete_budget(self, fund_id: int, month: str) -> None:
        """Remove a month override so the fund's default applies again."""
        self.conn.execute("DELETE FROM budgets WHERE fund_id = ? AND month = ?", (fund_id, month))

    # --- carry adjustments ---
    def add_carry(self, adj: CarryAdjustment) -> CarryAdjustment:
        cur = self.conn.execute(
            """INSERT INTO carry_adjustments(fund_id, month, amount, source_month, kind, emi_remaining)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (adj.fund_id, adj.month, adj.amount, adj.source_month, adj.kind, adj.emi_remaining),
        )
        adj.id = cur.lastrowid
        return adj

    def delete_carry_by_source(self, source_month: str) -> None:
        self.conn.execute("DELETE FROM carry_adjustments WHERE source_month = ?", (source_month,))

    def sum_carry(self, fund_id: int, month: str) -> float:
        r = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM carry_adjustments WHERE fund_id = ? AND month = ?",
            (fund_id, month),
        ).fetchone()
        return float(r["s"])

    def list_carry(self, fund_id: int, month: str) -> list[CarryAdjustment]:
        rows = self.conn.execute(
            "SELECT * FROM carry_adjustments WHERE fund_id = ? AND month = ? ORDER BY id",
            (fund_id, month),
        ).fetchall()
        return [
            CarryAdjustment(
                id=r["id"], fund_id=r["fund_id"], month=r["month"], amount=r["amount"],
                source_month=r["source_month"], kind=r["kind"], emi_remaining=r["emi_remaining"],
            )
            for r in rows
        ]
