"""API request/response DTOs (pydantic). Kept separate from domain models."""
from pydantic import BaseModel, Field


# --- auth / meta ---
class LoginRequest(BaseModel):
    user_id: int
    password: str


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str


# --- profiles / users ---
class ProfileOut(BaseModel):
    id: int
    name: str
    avatar: str | None = None


class WhoAmI(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    is_admin: bool
    must_change_password: bool


class UserOut(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    is_admin: bool
    must_change_password: bool
    created_at: str | None = None


class CreateUserIn(BaseModel):
    name: str
    password: str
    avatar: str | None = None
    is_admin: bool = False


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordIn(BaseModel):
    new_password: str


class AvatarIn(BaseModel):
    avatar: str | None = None


# --- funds ---
class FundIn(BaseModel):
    name: str
    color: str | None = None
    sort: int = 0
    active: bool = True
    default_amount: float = 0.0
    default_carry_underspend: bool = False
    default_carry_overspend: bool = False
    default_emi_months: int = 1


class FundOut(BaseModel):
    id: int
    name: str
    color: str | None = None
    sort: int = 0
    active: bool = True
    default_amount: float = 0.0
    default_carry_underspend: bool = False
    default_carry_overspend: bool = False
    default_emi_months: int = 1


# --- labels / groups ---
class LabelIn(BaseModel):
    name: str
    color: str | None = None


class LabelOut(BaseModel):
    id: int
    name: str
    color: str | None = None


class GroupIn(BaseModel):
    name: str
    label_ids: list[int] = Field(default_factory=list)


class GroupOut(BaseModel):
    id: int
    name: str
    label_ids: list[int]


# --- expenses ---
class ExpenseIn(BaseModel):
    amount: float
    fund_id: int
    labels: list[str] = Field(default_factory=list)  # names; created on the fly
    ts: str | None = None
    note: str | None = None


class ExpenseOut(BaseModel):
    id: int
    ts: str
    amount: float
    fund_id: int
    note: str | None = None
    label_ids: list[int]


# --- budgets ---
class BudgetIn(BaseModel):
    amount: float = 0.0
    carry_underspend: bool = False
    carry_overspend: bool = False
    emi_months: int = 1


class BudgetOut(BudgetIn):
    fund_id: int
    month: str
    is_override: bool = False


# --- transfers (siphon) ---
class TransferIn(BaseModel):
    month: str
    from_fund_id: int
    to_fund_id: int
    amount: float
    reason: str | None = None
    trigger_expense_id: int | None = None


class TransferOut(BaseModel):
    id: int
    month: str
    from_fund_id: int
    to_fund_id: int
    amount: float
    reason: str | None = None
    trigger_expense_id: int | None = None
    ts: str
