"""Budgets, the monthly overview, fund detail, siphon transfers,
balance suggestions, and month-close."""
from fastapi import APIRouter, Depends, Query

from ..auth import require_auth
from ..deps import budget_service, transfer_service
from ..schemas import BudgetIn, BudgetOut, MessageResponse, TransferIn, TransferOut
from ..services.budget_service import BudgetService
from ..services.transfer_service import TransferService

router = APIRouter(tags=["budgets"], dependencies=[Depends(require_auth)])


@router.get("/budgets/{fund_id}", response_model=BudgetOut)
def get_budget(fund_id: int, month: str, svc: BudgetService = Depends(budget_service)):
    b, is_override = svc.get_budget(fund_id, month)
    return BudgetOut(**b.__dict__, is_override=is_override)


@router.put("/budgets/{fund_id}", response_model=BudgetOut)
def set_budget(fund_id: int, month: str, body: BudgetIn, svc: BudgetService = Depends(budget_service)):
    """Sets a per-month override for this fund."""
    b = svc.set_override(fund_id, month, body.amount, body.carry_underspend,
                         body.carry_overspend, body.emi_months)
    return BudgetOut(**b.__dict__, is_override=True)


@router.delete("/budgets/{fund_id}", response_model=MessageResponse)
def clear_budget_override(fund_id: int, month: str, svc: BudgetService = Depends(budget_service)):
    """Removes the month override so the fund's default applies again."""
    svc.clear_override(fund_id, month)
    return MessageResponse(message="reverted to default")


@router.get("/overview")
def overview(month: str, svc: BudgetService = Depends(budget_service)) -> list[dict]:
    return svc.overview(month)


@router.get("/funds/{fund_id}/detail")
def fund_detail(fund_id: int, month: str, svc: BudgetService = Depends(budget_service)) -> dict:
    return svc.fund_detail(fund_id, month)


@router.get("/funds/{fund_id}/balance-suggestions")
def balance_suggestions(fund_id: int, month: str, svc: BudgetService = Depends(budget_service)) -> list[dict]:
    return svc.balance_suggestions(fund_id, month)


@router.post("/months/{month}/close")
def close_month(month: str, svc: BudgetService = Depends(budget_service)) -> dict:
    return svc.close_month(month)


@router.get("/heatmap")
def heatmap(months: list[str] = Query(...), svc: BudgetService = Depends(budget_service)) -> dict:
    return svc.heatmap(months)


@router.get("/history")
def history(svc: BudgetService = Depends(budget_service)) -> dict:
    return svc.history()


@router.post("/transfers", response_model=TransferOut)
def create_transfer(body: TransferIn, svc: TransferService = Depends(transfer_service)):
    t = svc.create(body.month, body.from_fund_id, body.to_fund_id, body.amount,
                   body.reason, body.trigger_expense_id)
    return TransferOut(**t.__dict__)


@router.get("/transfers", response_model=list[TransferOut])
def list_transfers(month: str, svc: TransferService = Depends(transfer_service)):
    return [TransferOut(**t.__dict__) for t in svc.list_for_month(month)]
