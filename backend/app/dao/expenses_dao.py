"""SQL for expenses and their label attachments."""
import sqlite3

from ..models import Expense


class ExpensesDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _row(r: sqlite3.Row) -> Expense:
        return Expense(id=r["id"], ts=r["ts"], amount=r["amount"], fund_id=r["fund_id"], note=r["note"])

    def create(self, e: Expense) -> Expense:
        cur = self.conn.execute(
            "INSERT INTO expenses(ts, amount, fund_id, note) VALUES (?, ?, ?, ?)",
            (e.ts, e.amount, e.fund_id, e.note),
        )
        e.id = cur.lastrowid
        return e

    def get(self, expense_id: int) -> Expense | None:
        r = self.conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        if not r:
            return None
        e = self._row(r)
        e.label_ids = self.label_ids(expense_id)
        return e

    def update(self, e: Expense) -> Expense:
        self.conn.execute(
            "UPDATE expenses SET ts = ?, amount = ?, fund_id = ?, note = ? WHERE id = ?",
            (e.ts, e.amount, e.fund_id, e.note, e.id),
        )
        return e

    def delete(self, expense_id: int) -> None:
        self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

    def set_labels(self, expense_id: int, label_ids: list[int]) -> None:
        self.conn.execute("DELETE FROM expense_labels WHERE expense_id = ?", (expense_id,))
        self.conn.executemany(
            "INSERT INTO expense_labels(expense_id, label_id) VALUES (?, ?)",
            [(expense_id, lid) for lid in label_ids],
        )

    def label_ids(self, expense_id: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT label_id FROM expense_labels WHERE expense_id = ?", (expense_id,)
        ).fetchall()
        return [r["label_id"] for r in rows]

    def list(
        self,
        month: str | None = None,
        fund_id: int | None = None,
        label_ids: list[int] | None = None,
        months: list[str] | None = None,
    ) -> list[Expense]:
        """label_ids uses AND semantics — an expense must carry all of them.
        `months` (a list) takes precedence over the single `month`."""
        clauses, params = [], []
        if months:
            marks = ",".join("?" * len(months))
            clauses.append(f"substr(e.ts, 1, 7) IN ({marks})")
            params.extend(months)
        elif month:
            clauses.append("substr(e.ts, 1, 7) = ?")
            params.append(month)
        if fund_id:
            clauses.append("e.fund_id = ?")
            params.append(fund_id)
        if label_ids:
            marks = ",".join("?" * len(label_ids))
            clauses.append(
                f"e.id IN (SELECT expense_id FROM expense_labels WHERE label_id IN ({marks}) "
                f"GROUP BY expense_id HAVING COUNT(DISTINCT label_id) = ?)"
            )
            params.extend(label_ids)
            params.append(len(label_ids))
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.conn.execute(
            f"SELECT * FROM expenses e{where} ORDER BY e.ts DESC, e.id DESC", params
        ).fetchall()
        result = []
        for r in rows:
            e = self._row(r)
            e.label_ids = self.label_ids(e.id)
            result.append(e)
        return result

    def sum_by_fund_month(self, fund_id: int, month: str) -> float:
        r = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM expenses WHERE fund_id = ? AND substr(ts, 1, 7) = ?",
            (fund_id, month),
        ).fetchone()
        return float(r["s"])

    def count_by_fund(self, fund_id: int) -> int:
        r = self.conn.execute("SELECT COUNT(*) AS c FROM expenses WHERE fund_id = ?", (fund_id,)).fetchone()
        return int(r["c"])

    def earliest_month(self) -> str | None:
        r = self.conn.execute("SELECT substr(MIN(ts), 1, 7) AS m FROM expenses").fetchone()
        return r["m"]
