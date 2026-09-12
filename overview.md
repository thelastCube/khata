Told AI to write this.

---

# khata — overview

A personal ledger for your money. Single user. You set a monthly budget per fund,
log expenses as they happen, and khata shows which funds are over, by how much, and
how to balance them. Cozy, minimal, boring on purpose.

---

## The mental model — three things

- **Funds** — your money buckets, each with a monthly budget (Rent, Food, Hobbies…).
  Every expense is charged to **exactly one** fund.
- **Labels** — free tags you stick on an expense (`groceries`, `friend`, `trip-goa`).
  Any number per expense. Labels cut *across* funds, so you can ask "how much on
  dining out?" even when it's split over Food and Outings. Matching is
  case-insensitive (`Food` = `food`); the name keeps the case you gave it and can be
  renamed anytime. A new label is created automatically the first time you use it.
- **Groups** — a saved set of labels, so you can filter by them in one tap.

---

## The sections

- **add** (the landing page) — fast expense entry: amount, fund, labels
  (autocomplete — pick a suggestion or press Enter to create), date, optional note.
  This is the screen you'll use daily.
- **overview** — funds sorted **most-exceeded first**. Each card shows the spend as a
  big number (green under budget, red over), a bar that fills green (full red when
  exceeded), and stat attributes: `budget`, `left`/`exceeded`, `carried over`,
  `siphoned in`. A **close [month]** button sits at the bottom.
- **fund detail** (tap any fund) — every expense with timestamps + labels, spend vs
  budget, **delta vs last month**, a **"balance this overage"** button, and a
  traceability list of siphons and carryover.
- **analyse** — pick any labels (an expense must have *all* selected), a group, or a
  fund; get the total, count, and breakdowns by fund and by label. When limited to a
  month, each fund also shows its budget and over/left/carryover.
- **settings** — funds + their **default budgets** and per-month **overrides**, the
  carry toggles, labels, groups, the three **fonts** (headings / body / amounts), and
  **CSV backup**.
- **log** — a plain-language audit timeline of everything that happened.
- **khata** (top-left) — opens **the words, simply**: a glossary in everyday terms.

Top-right of the nav: the **month picker** (dropdown → year + month grid), a
**light/dark toggle**, and **out** (logout).

---

## How you'd actually use it

1. **Settings → funds**: add your funds and give each a **default monthly budget**.
   Flip the carry toggles where you want them (see below). Override a month only when
   something's unusual.
2. **Add** an expense whenever you spend. Tag it.
3. **Overview** to see where you stand; tap a fund for detail.
4. If a fund's red, open it → **balance this overage** → khata suggests funds with
   spare budget; **siphon** from one. It's logged and traceable.
5. End of month → **close [month]** to apply carryover per your toggles.

---

## The words, simply

- **budget** — how much you plan to spend from a fund in a month. Each fund has a
  default that repeats; override it for one month when needed.
- **spent** — what you actually spent this month.
- **left** — budget minus spent (green).
- **exceeded** — how much you went over (red).
- **siphoned** — moving spare budget from one fund to cover another that went over
  (blue). Example: Hobbies has spare, Food is over → siphon Hobbies → Food.
- **carried over** — at month-end, a fund's result can flow into next month. Two
  flavours: underspend **rolls forward** (next month has a bit more); overspend
  **trims** next month to make up for it (optionally spread over a few months,
  EMI-style). Off by default; switch it on per fund.
- **close the month** — the button that applies carryover. Nothing rolls forward
  until you close. Safe to run again; it just recalculates.

---

## Run it

**Backend** (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # set APP_PASSWORD + SECRET_KEY
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)
python seed.py                # optional: wipe DB + load mock demo data
```

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Log in with your `APP_PASSWORD`, and you'll land on the **add** page. If you seeded,
open **overview** to see a demo month.
