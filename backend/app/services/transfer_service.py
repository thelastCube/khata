"""Siphon transfers: move budget from a surplus fund to cover another.
Validates the source actually has the surplus (uses BudgetService)."""
from ..dao.audit_dao import AuditDao
from ..dao.funds_dao import FundsDao
from ..dao.transfers_dao import TransfersDao
from ..models import Transfer
from ..util import now_iso
from .budget_service import BudgetService


class TransferError(ValueError):
    pass


class TransferService:
    def __init__(self, transfers: TransfersDao, funds: FundsDao, budget: BudgetService, audit: AuditDao):
        self.transfers = transfers
        self.funds = funds
        self.budget = budget
        self.audit = audit

    def create(self, month: str, from_fund_id: int, to_fund_id: int, amount: float,
               reason: str | None = None, trigger_expense_id: int | None = None) -> Transfer:
        if amount <= 0:
            raise TransferError("amount must be positive")
        if from_fund_id == to_fund_id:
            raise TransferError("cannot transfer a fund into itself")
        if not self.funds.get(from_fund_id) or not self.funds.get(to_fund_id):
            raise TransferError("source or destination fund not found")
        source = self.budget.compute(from_fund_id, month)
        if source["remaining"] < amount:
            raise TransferError(
                f"source fund only has {source['remaining']:.2f} spare, cannot move {amount:.2f}"
            )
        t = self.transfers.create(Transfer(
            month=month, from_fund_id=from_fund_id, to_fund_id=to_fund_id, amount=amount,
            reason=reason, trigger_expense_id=trigger_expense_id, ts=now_iso()))
        self.audit.log("transfer.create", "transfer", t.id,
                       {"month": month, "from": from_fund_id, "to": to_fund_id, "amount": amount,
                        "reason": reason, "trigger_expense_id": trigger_expense_id})
        return t

    def list_for_month(self, month: str) -> list[Transfer]:
        return self.transfers.list_for_month(month)
