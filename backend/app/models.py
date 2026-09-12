"""Domain models — the shared vocabulary between DAOs and services.
Plain dataclasses; not tied to the DB row shape or the API DTOs.
Timestamps are ISO8601 strings; months are 'YYYY-MM' strings."""
from dataclasses import dataclass, field


@dataclass
class Fund:
    name: str
    id: int | None = None
    color: str | None = None
    sort: int = 0
    active: bool = True
    default_amount: float = 0.0
    default_carry_underspend: bool = False
    default_carry_overspend: bool = False
    default_emi_months: int = 1


@dataclass
class Label:
    name: str
    id: int | None = None
    color: str | None = None


@dataclass
class Expense:
    amount: float
    fund_id: int
    ts: str
    id: int | None = None
    note: str | None = None
    label_ids: list[int] = field(default_factory=list)


@dataclass
class Budget:
    fund_id: int
    month: str  # YYYY-MM
    amount: float = 0.0
    carry_underspend: bool = False
    carry_overspend: bool = False
    emi_months: int = 1


@dataclass
class Transfer:
    month: str
    from_fund_id: int
    to_fund_id: int
    amount: float
    ts: str
    id: int | None = None
    reason: str | None = None
    trigger_expense_id: int | None = None


@dataclass
class CarryAdjustment:
    fund_id: int
    month: str
    amount: float
    kind: str  # 'underspend_rollin' | 'overspend_repay'
    id: int | None = None
    source_month: str | None = None
    emi_remaining: int = 0
