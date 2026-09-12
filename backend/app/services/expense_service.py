"""Expense create/update/delete/list. Labels are passed by name and
resolved (created on the fly) via LabelService."""
from ..dao.audit_dao import AuditDao
from ..dao.expenses_dao import ExpensesDao
from ..dao.funds_dao import FundsDao
from ..models import Expense
from ..util import now_iso
from .label_service import LabelService


class ExpenseError(ValueError):
    pass


class ExpenseService:
    def __init__(self, expenses: ExpensesDao, funds: FundsDao, labels: LabelService, audit: AuditDao):
        self.expenses = expenses
        self.funds = funds
        self.labels = labels
        self.audit = audit

    def _check_fund(self, fund_id: int) -> None:
        if not self.funds.get(fund_id):
            raise ExpenseError(f"fund {fund_id} not found")

    def create(self, amount: float, fund_id: int, label_names: list[str],
               ts: str | None = None, note: str | None = None) -> Expense:
        if amount <= 0:
            raise ExpenseError("amount must be positive")
        self._check_fund(fund_id)
        e = self.expenses.create(Expense(amount=amount, fund_id=fund_id, ts=ts or now_iso(), note=note))
        label_ids = self.labels.resolve_names(label_names)
        self.expenses.set_labels(e.id, label_ids)
        e.label_ids = label_ids
        self.audit.log("expense.create", "expense", e.id,
                       {"amount": amount, "fund_id": fund_id, "labels": label_names})
        return e

    def update(self, expense_id: int, amount: float, fund_id: int,
               label_names: list[str], ts: str | None, note: str | None) -> Expense:
        e = self.expenses.get(expense_id)
        if not e:
            raise ExpenseError(f"expense {expense_id} not found")
        if amount <= 0:
            raise ExpenseError("amount must be positive")
        self._check_fund(fund_id)
        e.amount, e.fund_id, e.note = amount, fund_id, note
        if ts:
            e.ts = ts
        self.expenses.update(e)
        label_ids = self.labels.resolve_names(label_names)
        self.expenses.set_labels(expense_id, label_ids)
        e.label_ids = label_ids
        self.audit.log("expense.update", "expense", expense_id, {"amount": amount, "fund_id": fund_id})
        return e

    def delete(self, expense_id: int) -> None:
        e = self.expenses.get(expense_id)
        if not e:
            raise ExpenseError(f"expense {expense_id} not found")
        self.expenses.delete(expense_id)
        self.audit.log("expense.delete", "expense", expense_id, {"amount": e.amount})

    def get(self, expense_id: int) -> Expense:
        e = self.expenses.get(expense_id)
        if not e:
            raise ExpenseError(f"expense {expense_id} not found")
        return e

    def list(self, month: str | None = None, fund_id: int | None = None,
             label_ids: list[int] | None = None) -> list[Expense]:
        return self.expenses.list(month=month, fund_id=fund_id, label_ids=label_ids)
