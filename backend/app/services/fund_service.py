"""Fund CRUD, including each fund's default monthly budget. Deleting a
fund that has expenses deactivates it instead, so history stays intact."""
from ..dao.audit_dao import AuditDao
from ..dao.expenses_dao import ExpensesDao
from ..dao.funds_dao import FundsDao
from ..models import Fund


class FundError(ValueError):
    pass


class FundService:
    def __init__(self, funds: FundsDao, expenses: ExpensesDao, audit: AuditDao):
        self.funds = funds
        self.expenses = expenses
        self.audit = audit

    def list(self, include_inactive: bool = False) -> list[Fund]:
        return self.funds.list(include_inactive)

    def get(self, fund_id: int) -> Fund:
        f = self.funds.get(fund_id)
        if not f:
            raise FundError(f"fund {fund_id} not found")
        return f

    def create(self, name: str, color: str | None, sort: int, default_amount: float = 0.0,
               default_carry_underspend: bool = False, default_carry_overspend: bool = False,
               default_emi_months: int = 1) -> Fund:
        if self.funds.get_by_name(name):
            raise FundError(f"fund '{name}' already exists")
        f = self.funds.create(Fund(
            name=name, color=color, sort=sort, default_amount=default_amount,
            default_carry_underspend=default_carry_underspend,
            default_carry_overspend=default_carry_overspend, default_emi_months=default_emi_months))
        self.audit.log("fund.create", "fund", f.id, {"name": name, "default_amount": default_amount})
        return f

    def update(self, fund_id: int, name: str, color: str | None, sort: int, active: bool,
               default_amount: float = 0.0, default_carry_underspend: bool = False,
               default_carry_overspend: bool = False, default_emi_months: int = 1) -> Fund:
        f = self.get(fund_id)
        clash = self.funds.get_by_name(name)
        if clash and clash.id != fund_id:
            raise FundError(f"fund '{name}' already exists")
        f.name, f.color, f.sort, f.active = name, color, sort, active
        f.default_amount = default_amount
        f.default_carry_underspend = default_carry_underspend
        f.default_carry_overspend = default_carry_overspend
        f.default_emi_months = default_emi_months
        self.funds.update(f)
        self.audit.log("fund.update", "fund", fund_id, {"name": name, "active": active})
        return f

    def delete(self, fund_id: int) -> str:
        f = self.get(fund_id)
        if self.expenses.count_by_fund(fund_id) > 0:
            f.active = False
            self.funds.update(f)
            self.audit.log("fund.deactivate", "fund", fund_id, {"reason": "has expenses"})
            return "deactivated"
        self.funds.delete(fund_id)
        self.audit.log("fund.delete", "fund", fund_id, {"name": f.name})
        return "deleted"
