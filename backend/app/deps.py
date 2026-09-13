"""Dependency wiring: build DAOs and services bound to the per-request
connection. Routers depend on services, never on DAOs directly."""
import sqlite3

from fastapi import Depends

from .auth_db import get_auth_db
from .config import Settings, get_settings
from .dao.audit_dao import AuditDao
from .dao.budgets_dao import BudgetsDao
from .dao.expenses_dao import ExpensesDao
from .dao.funds_dao import FundsDao
from .dao.labels_dao import LabelsDao
from .dao.transfers_dao import TransfersDao
from .db import get_db
from .services.analysis_service import AnalysisService
from .services.audit_service import AuditService
from .services.backup_service import BackupService
from .services.budget_service import BudgetService
from .services.expense_service import ExpenseService
from .services.fund_service import FundService
from .services.label_service import LabelService
from .services.transfer_service import TransferService
from .services.user_service import UserService
from .dao.users_dao import UsersDao


def fund_service(conn: sqlite3.Connection = Depends(get_db)) -> FundService:
    return FundService(FundsDao(conn), ExpensesDao(conn), AuditDao(conn))


def label_service(conn: sqlite3.Connection = Depends(get_db)) -> LabelService:
    return LabelService(LabelsDao(conn), AuditDao(conn))


def expense_service(conn: sqlite3.Connection = Depends(get_db)) -> ExpenseService:
    return ExpenseService(ExpensesDao(conn), FundsDao(conn),
                          LabelService(LabelsDao(conn), AuditDao(conn)), AuditDao(conn))


def budget_service(conn: sqlite3.Connection = Depends(get_db)) -> BudgetService:
    return BudgetService(FundsDao(conn), BudgetsDao(conn), ExpensesDao(conn),
                         TransfersDao(conn), AuditDao(conn))


def transfer_service(conn: sqlite3.Connection = Depends(get_db)) -> TransferService:
    budget = BudgetService(FundsDao(conn), BudgetsDao(conn), ExpensesDao(conn),
                           TransfersDao(conn), AuditDao(conn))
    return TransferService(TransfersDao(conn), FundsDao(conn), budget, AuditDao(conn))


def analysis_service(conn: sqlite3.Connection = Depends(get_db)) -> AnalysisService:
    return AnalysisService(ExpensesDao(conn), FundsDao(conn), LabelsDao(conn))


def audit_service(conn: sqlite3.Connection = Depends(get_db)) -> AuditService:
    return AuditService(AuditDao(conn))


def backup_service(conn: sqlite3.Connection = Depends(get_db)) -> BackupService:
    return BackupService(conn)


def user_service(auth_conn: sqlite3.Connection = Depends(get_auth_db),
                 settings: Settings = Depends(get_settings)) -> UserService:
    return UserService(UsersDao(auth_conn), settings)
