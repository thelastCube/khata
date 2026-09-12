# budget app — implementation plan

I told Claude the idea, structure, design, architecture. It wrote this which sounds more structured, so will include this in commit

**Stack:** Python + FastAPI backend, SQLite (single file), React + Vite PWA frontend
(swappable), single-user auth.

---

## Architecture — the one rule

Strict layering, top calls down only:

```
api  →  services  →  dao  →  sqlite
```

- **api** (routers): thin. Parse request, call a service, return a DTO. No logic.
- **services**: all business logic — budget math, carryover engine, siphon, analysis.
  Call DAOs. **Never write SQL.**
- **dao**: the *only* layer that touches the DB. Returns domain objects, not raw rows.

SOLID, pragmatically: DAOs are the seam services depend on (testable, swappable),
each service is single-responsibility. No abstract base classes, no DI framework —
plain function/constructor injection where it earns its place.

---

## Repo layout

```
budget/
  backend/
    app/
      main.py           # app wiring, router mounts, auth dep
      config.py         # env: SECRET, DB_PATH, BACKUP_REPO
      db.py             # connection + schema init / migrations
      auth.py           # single-user auth dependency
      schemas.py        # pydantic request/response DTOs
      models.py         # domain models (plain dataclasses)
      dao/              # ONLY layer with SQL
        funds_dao.py   expenses_dao.py   labels_dao.py
        budgets_dao.py transfers_dao.py  audit_dao.py
      services/         # logic; call DAOs, no SQL
        expense_service.py  budget_service.py  label_service.py
        analysis_service.py audit_service.py   backup_service.py
      api/              # thin routers
        expenses.py funds.py budgets.py labels.py analysis.py audit.py
    tests/
    pyproject.toml
  frontend/             # Vite PWA
  data/                 # sqlite file + csv exports
```

---

## Data model (SQLite)

- `funds`(id, name, color, sort, active)
- `budgets`(fund_id, month `YYYY-MM`, amount, carry_underspend, carry_overspend, emi_months)
  — one row per fund per active month
- `expenses`(id, ts, amount, fund_id, note) — **one fund per expense** (the budget bucket)
- `labels`(id, name, color)
- `expense_labels`(expense_id, label_id) — many-to-many
- `groups`(id, name)
- `group_labels`(group_id, label_id)
- `transfers`(id, month, from_fund_id, to_fund_id, amount, reason, trigger_expense_id?, ts)
  — the siphon record
- `carry_adjustments`(id, fund_id, month, amount, source_month, kind, emi_remaining)
  — opening adjustments the engine writes; EMI repayment schedule lives here
- `audit_log`(id, ts, action, entity, entity_id, detail_json) — powers the UI timeline

**Funds vs labels:** two separate axes. A *fund* is the budgeted bucket an expense is
charged to (used for compare + siphon). *Labels* are free cross-cutting tags for analysis
(food, friend, "trip nov 2026"). *Groups* are saved sets of labels.

---

## Budget engine (`budget_service`)

- `available = budget.amount + Σ carry_adjustments + transfers_in − transfers_out`
- `spent    = Σ expenses(fund, month)`
- `remaining = available − spent` · `overage = max(0, −remaining)`

**Month close:**
- Underspend + `carry_underspend` on → write `carry_adjustment(+remaining)` into next
  month (same fund, or reassign).
- Overspend → carries **nothing by default**. With `carry_overspend` on → repay next
  month, or split `overage / emi_months` across N months (EMI-style).
- Every step writes `audit_log`, so the UI can explain e.g. *"Hobbies is ₹4,500 not
  ₹5,000 — repaying Oct's ₹500 overspend over 1 month."*

**Siphon:** `POST /transfers` moves budget from a surplus fund to an exceeded one
(validated: source must have surplus), logged, optionally linked to the triggering
expense. That is the "this expense ate into its own budget *and* this other one" trace.

---

## API surface

- Expenses CRUD · `GET /expenses?month=&fund=&labels=&group=`
- `GET /overview?month=` — funds sorted by overage, with budget / spent / exceeded /
  carryover pills
- `GET /funds/{id}?month=` — detail: expenses w/ timestamps, spent vs budget, overage,
  delta vs last month, transfers in/out
- `GET /funds/{id}/balance-suggestions?month=` — surplus funds to siphon from
- `POST /transfers` — siphon
- CRUD `/funds` `/labels` `/groups`
- Budgets get/put · `POST /months/{month}/close`
- `GET /analysis?labels=&group=&month=` — cross-cut totals
- `GET /audit?entity=&month=` — human-readable log

**Auth:** one secret in env → login sets a signed HTTP-only cookie; a FastAPI dependency
guards every route. HTTPS at the host. Nothing more.

**Backup:** `backup_service` exports tables → CSV in `data/exports/` and commits + pushes
to a private git repo (scheduled + after writes). The SQLite file is itself copy-to-backup.

---

## UI

Minimalist but cozy. Big fonts, simple numbers. **Fraunces** for headings (warm,
characterful), **JetBrains Mono** for all amounts (a ledger that lines up). Warm off-white
ground. Pills: budget, **exceeded in red**, carryover in a darker shade of the same hue.

Pages: (1) add-expense fast entry, (2) overview sorted by overage, (3) fund detail,
(4) label/group filter + cross-cut totals, (5) settings (funds/labels/groups CRUD,
carry toggles, fonts), (6) audit timeline.