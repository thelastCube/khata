"""The budget engine: effective-budget resolution (per-month override →
fund default), available/spent/overage math, the monthly overview, fund
detail, siphon-balance suggestions, and month-close carryover.

available = budget.amount + carry_adjustments + transfers_in - transfers_out
spent     = sum of the fund's expenses that month
remaining = available - spent   ·   overage = max(0, -remaining)
"""
from ..dao.audit_dao import AuditDao
from ..dao.budgets_dao import BudgetsDao
from ..dao.expenses_dao import ExpensesDao
from ..dao.funds_dao import FundsDao
from ..dao.transfers_dao import TransfersDao
from ..models import Budget, CarryAdjustment
from ..util import add_months


class BudgetError(ValueError):
    pass


class BudgetService:
    def __init__(self, funds: FundsDao, budgets: BudgetsDao, expenses: ExpensesDao,
                 transfers: TransfersDao, audit: AuditDao):
        self.funds = funds
        self.budgets = budgets
        self.expenses = expenses
        self.transfers = transfers
        self.audit = audit

    def effective_budget(self, fund_id: int, month: str) -> tuple[Budget, bool]:
        """Return (budget, is_override). A per-month row overrides the fund's default."""
        override = self.budgets.get_budget(fund_id, month)
        if override:
            return override, True
        f = self.funds.get(fund_id)
        if not f:
            raise BudgetError(f"fund {fund_id} not found")
        return Budget(fund_id=fund_id, month=month, amount=f.default_amount,
                      carry_underspend=f.default_carry_underspend,
                      carry_overspend=f.default_carry_overspend,
                      emi_months=f.default_emi_months), False

    def get_budget(self, fund_id: int, month: str) -> tuple[Budget, bool]:
        return self.effective_budget(fund_id, month)

    def compute(self, fund_id: int, month: str) -> dict:
        b, _ = self.effective_budget(fund_id, month)
        base = b.amount
        carry = self.budgets.sum_carry(fund_id, month)
        t_in = self.transfers.sum_in(fund_id, month)
        t_out = self.transfers.sum_out(fund_id, month)
        available = base + carry + t_in - t_out
        spent = self.expenses.sum_by_fund_month(fund_id, month)
        remaining = available - spent
        return {
            "fund_id": fund_id, "month": month, "base": base, "carry": carry,
            "transfers_in": t_in, "transfers_out": t_out, "available": available,
            "spent": spent, "remaining": remaining, "overage": max(0.0, -remaining),
        }

    def set_override(self, fund_id: int, month: str, amount: float, carry_underspend: bool,
                     carry_overspend: bool, emi_months: int) -> Budget:
        if not self.funds.get(fund_id):
            raise BudgetError(f"fund {fund_id} not found")
        if emi_months < 1:
            raise BudgetError("emi_months must be >= 1")
        b = Budget(fund_id=fund_id, month=month, amount=amount, carry_underspend=carry_underspend,
                   carry_overspend=carry_overspend, emi_months=emi_months)
        self.budgets.upsert_budget(b)
        self.audit.log("budget.override", "fund", fund_id, {"month": month, "amount": amount})
        return b

    def clear_override(self, fund_id: int, month: str) -> None:
        self.budgets.delete_budget(fund_id, month)
        self.audit.log("budget.clear_override", "fund", fund_id, {"month": month})

    def overview(self, month: str) -> list[dict]:
        """One row per active fund, most-exceeded first."""
        rows = []
        for f in self.funds.list():
            b, is_override = self.effective_budget(f.id, month)
            c = self.compute(f.id, month)
            c["fund"] = {"id": f.id, "name": f.name, "color": f.color}
            c["is_override"] = is_override
            c["carry_underspend"] = b.carry_underspend
            c["carry_overspend"] = b.carry_overspend
            c["emi_months"] = b.emi_months
            rows.append(c)
        rows.sort(key=lambda r: (-r["overage"], r["remaining"]))
        return rows

    def fund_detail(self, fund_id: int, month: str) -> dict:
        f = self.funds.get(fund_id)
        if not f:
            raise BudgetError(f"fund {fund_id} not found")
        b, is_override = self.effective_budget(fund_id, month)
        c = self.compute(fund_id, month)
        prev_month = add_months(month, -1)
        prev_spent = self.expenses.sum_by_fund_month(fund_id, prev_month)
        expenses = self.expenses.list(month=month, fund_id=fund_id)
        transfers = self.transfers.list_for_fund(fund_id, month)
        carry = self.budgets.list_carry(fund_id, month)
        fund_names = {x.id: x.name for x in self.funds.list(include_inactive=True)}
        c.update({
            "fund": {"id": f.id, "name": f.name, "color": f.color},
            "is_override": is_override,
            "carry_underspend": b.carry_underspend,
            "carry_overspend": b.carry_overspend,
            "emi_months": b.emi_months,
            "prev_spent": prev_spent,
            "delta_vs_prev": c["spent"] - prev_spent,
            "expenses": [
                {"id": e.id, "ts": e.ts, "amount": e.amount, "note": e.note, "label_ids": e.label_ids}
                for e in expenses
            ],
            "transfers": [
                {"id": t.id, "from_fund_id": t.from_fund_id, "to_fund_id": t.to_fund_id,
                 "from_name": fund_names.get(t.from_fund_id), "to_name": fund_names.get(t.to_fund_id),
                 "amount": t.amount, "reason": t.reason, "ts": t.ts,
                 "direction": "in" if t.to_fund_id == fund_id else "out"}
                for t in transfers
            ],
            "carry_adjustments": [
                {"amount": a.amount, "kind": a.kind, "source_month": a.source_month,
                 "emi_remaining": a.emi_remaining}
                for a in carry
            ],
        })
        return c

    def balance_suggestions(self, fund_id: int, month: str) -> list[dict]:
        """Funds with a surplus this month you could siphon from."""
        out = []
        for f in self.funds.list():
            if f.id == fund_id:
                continue
            c = self.compute(f.id, month)
            if c["remaining"] > 0:
                out.append({"fund": {"id": f.id, "name": f.name, "color": f.color},
                            "surplus": c["remaining"]})
        out.sort(key=lambda r: -r["surplus"])
        return out

    def heatmap(self, months: list[str]) -> dict:
        """Final-state grid: for each fund and month, budget vs spent and the
        net (budget - spent). Deliberately ignores carry/siphon — just whether
        you ended over or under, and by how much."""
        funds = self.funds.list()
        cells, totals = [], {m: {"base": 0.0, "spent": 0.0} for m in months}
        for m in months:
            for f in funds:
                b, _ = self.effective_budget(f.id, m)
                spent = self.expenses.sum_by_fund_month(f.id, m)
                cells.append({"month": m, "fund_id": f.id, "base": b.amount,
                              "spent": spent, "net": b.amount - spent})
                totals[m]["base"] += b.amount
                totals[m]["spent"] += spent
        return {
            "months": months,
            "funds": [{"id": f.id, "name": f.name} for f in funds],
            "cells": cells,
            "month_totals": [{"month": m, "base": totals[m]["base"], "spent": totals[m]["spent"],
                              "net": totals[m]["base"] - totals[m]["spent"]} for m in months],
        }

    def history(self, max_months: int = 120) -> dict:
        """Whole-month net for every month from the first expense to now."""
        from datetime import date
        today = date.today()
        cur = f"{today.year:04d}-{today.month:02d}"
        earliest = self.expenses.earliest_month() or cur
        months, m, guard = [], earliest, 0
        while m <= cur and guard < max_months:
            months.append(m)
            m = add_months(m, 1)
            guard += 1
        funds = self.funds.list()
        out = []
        for mm in months:
            base = spent = 0.0
            for f in funds:
                b, _ = self.effective_budget(f.id, mm)
                base += b.amount
                spent += self.expenses.sum_by_fund_month(f.id, mm)
            out.append({"month": mm, "base": base, "spent": spent, "net": base - spent})
        return {"months": months, "month_totals": out}

    def close_month(self, month: str) -> dict:
        """Compute each fund's leftover/overage and, where the toggles allow,
        write carry adjustments into future months. Idempotent — re-closing a
        month replaces the adjustments it produced."""
        self.budgets.delete_carry_by_source(month)
        applied = []
        for f in self.funds.list(include_inactive=True):
            b, _ = self.effective_budget(f.id, month)
            c = self.compute(f.id, month)
            nxt = add_months(month, 1)
            if c["remaining"] > 0 and b.carry_underspend:
                self.budgets.add_carry(CarryAdjustment(
                    fund_id=f.id, month=nxt, amount=c["remaining"], source_month=month,
                    kind="underspend_rollin", emi_remaining=0))
                applied.append({"fund_id": f.id, "kind": "underspend_rollin",
                                "amount": c["remaining"], "into": nxt})
            elif c["overage"] > 0 and b.carry_overspend:
                n = max(1, b.emi_months)
                per = round(c["overage"] / n, 2)
                for i in range(n):
                    m_i = add_months(month, i + 1)
                    self.budgets.add_carry(CarryAdjustment(
                        fund_id=f.id, month=m_i, amount=-per, source_month=month,
                        kind="overspend_repay", emi_remaining=n - 1 - i))
                applied.append({"fund_id": f.id, "kind": "overspend_repay",
                                "amount": c["overage"], "per_month": per, "months": n})
        self.audit.log("month.close", "month", None, {"month": month, "applied": applied})
        return {"month": month, "applied": applied}
