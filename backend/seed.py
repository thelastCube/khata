"""Wipe the DB and fill it with realistic mock data for a demo month.

Run from backend/ with the venv active:

    python seed.py

Populates the current month (some funds over budget, some under) and the
previous month, then closes the previous month so carryover shows up.
"""
import shutil
from datetime import date

from app.config import get_settings
from app.util import add_months
from app.dao.audit_dao import AuditDao
from app.dao.budgets_dao import BudgetsDao
from app.dao.expenses_dao import ExpensesDao
from app.dao.funds_dao import FundsDao
from app.dao.labels_dao import LabelsDao
from app.dao.transfers_dao import TransfersDao
from app.auth_db import auth_db_path, connect_auth, init_auth_db
from app.dao.users_dao import UsersDao
from app.db import connect, init_db, profile_db_path
from app.services.user_service import seed_default_admin
from app.services.budget_service import BudgetService
from app.services.expense_service import ExpenseService
from app.services.fund_service import FundService
from app.services.label_service import LabelService
from app.services.transfer_service import TransferService


def month_str(y, m):
    return f"{y:04d}-{m:02d}"


def main():
    today = date.today()
    cur = month_str(today.year, today.month)
    py, pm = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    prev = month_str(py, pm)

    settings = get_settings()
    # wipe the auth DB, legacy file, and every profile's data
    profiles_dir = settings.data_dir / "profiles"
    if profiles_dir.exists():
        shutil.rmtree(profiles_dir)
    for base in (auth_db_path(settings), settings.db_path):
        for suffix in ("", "-wal", "-shm"):
            p = base.parent / (base.name + suffix)
            if p.exists():
                p.unlink()

    # create the default admin profile, then write demo data into its DB
    init_auth_db(settings)
    seed_default_admin(settings)
    ac = connect_auth(settings)
    chai = UsersDao(ac).get_by_name("Chai")
    ac.close()
    data_path = profile_db_path(settings, chai.id)
    init_db(data_path)

    conn = connect(data_path)
    funds_dao, expenses_dao, labels_dao = FundsDao(conn), ExpensesDao(conn), LabelsDao(conn)
    budgets_dao, transfers_dao, audit = BudgetsDao(conn), TransfersDao(conn), AuditDao(conn)
    label_svc = LabelService(labels_dao, audit)
    fund_svc = FundService(funds_dao, expenses_dao, audit)
    expense_svc = ExpenseService(expenses_dao, funds_dao, label_svc, audit)
    budget_svc = BudgetService(funds_dao, budgets_dao, expenses_dao, transfers_dao, audit)
    transfer_svc = TransferService(transfers_dao, funds_dao, budget_svc, audit)

    # funds: name -> (budget, carry_underspend, carry_overspend, emi_months)
    plan = {
        "Rent": (15000, False, False, 1),
        "Food": (8000, False, True, 1),
        "Utilities": (3000, False, False, 1),
        "Hobbies": (4000, True, False, 1),
        "Travel": (3000, False, True, 2),
        "Outings": (5000, False, True, 1),
        "Subscriptions": (1500, False, False, 1),
        "Charity": (2000, False, False, 1),
    }
    funds = {}
    for name, (amt, under, over, emi) in plan.items():
        f = fund_svc.create(name, None, len(funds), amt, under, over, emi)
        funds[name] = f
    # one per-month override, to show overrides beating the default
    budget_svc.set_override(funds["Charity"].id, cur, 3000, False, False, 1)

    def spend(fund, amount, day, labels, note=None, mth=None):
        m = mth or cur
        expense_svc.create(amount, funds[fund].id, labels, ts=f"{m}-{day:02d}T13:30:00", note=note)

    # --- older history (cur-7 .. cur-2) so the heatmap / history views have data ---
    factors = [0.6, 1.2, 0.85, 1.35, 0.7, 1.1, 0.95]
    for k in range(7, 1, -1):
        hm = add_months(cur, -k)
        for idx, (name, (amt, *_rest)) in enumerate(plan.items()):
            f = factors[(idx + k) % len(factors)]
            spend(name, max(1, round(amt * f)), 15, ["seed"], mth=hm)

    # --- previous month: set up carryover ---
    # Hobbies under-spent (rolls forward), Travel over-spent (repays over 2 months).
    spend("Rent", 15000, 1, [], "monthly rent", mth=prev)
    spend("Food", 7200, 8, ["groceries"], "big grocery run", mth=prev)
    spend("Food", 900, 20, ["dining-out", "friend"], "dinner out", mth=prev)
    spend("Hobbies", 1500, 12, ["books"], "two novels", mth=prev)
    spend("Travel", 5000, 5, ["cab", "trip-goa"], "weekend trip", mth=prev)
    spend("Outings", 3200, 15, ["movie", "coffee"], mth=prev)
    budget_svc.close_month(prev)  # -> Hobbies +2500 into cur, Travel -1000 x2

    # --- current month ---
    spend("Rent", 15000, 1, [], "monthly rent")
    spend("Utilities", 1200, 3, ["electricity"], "electricity bill")
    spend("Utilities", 1400, 4, ["internet"], "broadband")
    spend("Food", 6800, 6, ["groceries"], "monthly groceries")
    spend("Food", 1300, 12, ["dining-out", "friend"], "lunch with a friend")
    spend("Food", 1100, 22, ["dining-out"], "takeout")  # pushes Food over 8000
    spend("Hobbies", 2500, 9, ["books", "coffee"], "books + cafe")
    spend("Travel", 2200, 7, ["cab"], "airport cab")
    spend("Outings", 2600, 10, ["movie", "coffee"], "movie night")
    spend("Outings", 3400, 18, ["dining-out", "friend"], "birthday dinner")  # Outings over 5000
    spend("Subscriptions", 1499, 2, ["ott"], "streaming + music")
    spend("Charity", 2000, 14, ["donation"], "monthly donation")

    # a group + a siphon to show balancing
    label_map = {label.name: label.id for label in labels_dao.list()}
    label_svc.create_group("outings", [label_map[n] for n in ("dining-out", "movie", "coffee", "cab") if n in label_map])
    # Hobbies has spare (rolled-in 2500), cover part of Food's overspend from it.
    transfer_svc.create(cur, funds["Hobbies"].id, funds["Food"].id, 800, reason="cover food overspend")

    conn.commit()
    conn.close()
    print(f"seeded profile 'Chai' (id={chai.id}): {len(funds)} funds, months {prev} and {cur} (current = {cur}).")
    print(f"auth db: {auth_db_path(settings)}")
    print(f"data db: {data_path}")


if __name__ == "__main__":
    main()
