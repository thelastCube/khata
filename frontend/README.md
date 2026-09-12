# khata — frontend

## Run (localhost)

Start the backend first (see `../backend/README.md`), then:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

localhost:5173 and localhost:8000 are same-site, so the login cookie flows.
If you run the backend on another origin, set it:

```bash
VITE_API_BASE=http://127.0.0.1:8000 npm run dev
```

## Pages

- **overview** — funds sorted by overage, budget/exceeded/carryover pills, close-month
- **add** — fast expense entry, labels created on the fly
- **fund detail** — expenses w/ timestamps, delta vs last month, siphon "balance this overage", traceability
- **analyse** — filter by any labels (AND) / group / fund, cross-cut totals
- **settings** — funds + per-month budgets & carry toggles, labels, groups, font, CSV backup
- **log** — audit timeline

## Build

```bash
npm run build        # -> dist/
```