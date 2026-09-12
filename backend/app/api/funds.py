"""Fund CRUD routes."""
from fastapi import APIRouter, Depends

from ..auth import require_auth
from ..deps import fund_service
from ..schemas import FundIn, FundOut, MessageResponse
from ..services.fund_service import FundService

router = APIRouter(prefix="/funds", tags=["funds"], dependencies=[Depends(require_auth)])


@router.get("", response_model=list[FundOut])
def list_funds(include_inactive: bool = False, svc: FundService = Depends(fund_service)):
    return [FundOut(**f.__dict__) for f in svc.list(include_inactive)]


@router.post("", response_model=FundOut)
def create_fund(body: FundIn, svc: FundService = Depends(fund_service)):
    f = svc.create(body.name, body.color, body.sort, body.default_amount,
                   body.default_carry_underspend, body.default_carry_overspend, body.default_emi_months)
    return FundOut(**f.__dict__)


@router.get("/{fund_id}", response_model=FundOut)
def get_fund(fund_id: int, svc: FundService = Depends(fund_service)):
    return FundOut(**svc.get(fund_id).__dict__)


@router.put("/{fund_id}", response_model=FundOut)
def update_fund(fund_id: int, body: FundIn, svc: FundService = Depends(fund_service)):
    f = svc.update(fund_id, body.name, body.color, body.sort, body.active, body.default_amount,
                   body.default_carry_underspend, body.default_carry_overspend, body.default_emi_months)
    return FundOut(**f.__dict__)


@router.delete("/{fund_id}", response_model=MessageResponse)
def delete_fund(fund_id: int, svc: FundService = Depends(fund_service)):
    return MessageResponse(message=svc.delete(fund_id))
