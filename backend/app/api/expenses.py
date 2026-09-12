"""Expense CRUD + filtered listing routes."""
from fastapi import APIRouter, Depends, Query

from ..auth import require_auth
from ..deps import expense_service
from ..schemas import ExpenseIn, ExpenseOut, MessageResponse
from ..services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"], dependencies=[Depends(require_auth)])


@router.post("", response_model=ExpenseOut)
def create_expense(body: ExpenseIn, svc: ExpenseService = Depends(expense_service)):
    e = svc.create(body.amount, body.fund_id, body.labels, body.ts, body.note)
    return ExpenseOut(**e.__dict__)


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    month: str | None = None,
    fund_id: int | None = None,
    label_ids: list[int] | None = Query(default=None),
    svc: ExpenseService = Depends(expense_service),
):
    return [ExpenseOut(**e.__dict__) for e in svc.list(month=month, fund_id=fund_id, label_ids=label_ids)]


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, svc: ExpenseService = Depends(expense_service)):
    return ExpenseOut(**svc.get(expense_id).__dict__)


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, body: ExpenseIn, svc: ExpenseService = Depends(expense_service)):
    e = svc.update(expense_id, body.amount, body.fund_id, body.labels, body.ts, body.note)
    return ExpenseOut(**e.__dict__)


@router.delete("/{expense_id}", response_model=MessageResponse)
def delete_expense(expense_id: int, svc: ExpenseService = Depends(expense_service)):
    svc.delete(expense_id)
    return MessageResponse(message="deleted")
