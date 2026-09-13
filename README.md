# khata
 
Khata (खाता) is a budget + expense tracker I (claude) made for myself. The whole idea was to log expenses on the fly and see how my bougee spending habits compare to what my big brain planned at the start of the month, at a glance. This repo contains the local web app, you can host it online or on that Pi that has been sitting in your drawer for 84 years

## what does it the do

- ✨ **P R O F I L E S** ✨ for your frens
- you can create ✨ **F U N D S** ✨ - buckets for your monthly budget. Think rent fund, hobby fund, food fund, tax fund 😭
  - You can set a default amount for every month, and also one off overrides for that month
  - If you have money left in your monthly fund or exceed it, you can carry it over to next month. If you want to adjust excess expense over multiple months not just next one, you can pay yourself in EMIs (or you can just forget about it like me). These are opt out by default, so every month starts with (an illusion of) a clean slate
  - Spent too much on that hobby keyboard? No worries, you can siphon off fund money from food fund and starve for a week to keep your number on screen not go red
- ✨ **L A B E L S** ✨ are, well, labels. You can add a `caffiene juice` label to an expense in food fund. These are mostly to sort data more granularly. Each expense needs to have one fund and can have as many labels 
- Use a combination of labels repeatedly? Why oh why don't you try ✨ **G R O U P S** ✨ which... are just a combination of labels
- There is also an analysis page with pretty ✨ **H E A T M A P S** ✨ with colours! Because obsessing over your github contribution histoy was not enough stress. You can sort expenses by month, two months, three months, year, by funds, by labels, compare two different months to feel better about yourself against yourself
- there is an audit log section and data lives in SQLite but can be exported to csv

## Stack

- **Backend** — Python, FastAPI, SQLite. Multi-profile cookie auth (hashed passwords, one data file per profile + a central auth db).
- **Frontend** — React + Vite

## Project structure

```
backend/          ze fastapi app
  app/
    api/          thin routers
    services/     business logic (budget engine, carryover, siphon, analysis)
    dao/          the only layer that has consent to touch DB
    db.py         schema + connection
    config.py     settings
  tests/          pytest tests
frontend/         React + Vite 
  src/pages/      ze frontend pages
plan.md           full design + hosting notes
```

## Run locally

**Backend** (needs Python 3.11+):

```bash
cd backend
python -m venv amogus          
source amogus/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # set APP_PASSWORD + SECRET_KEY
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)
pytest                        # run the tests
python seed.py                # optional: wipe DB + load mock demo data
```

**Frontend** (needs Node 18+):

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Log in with your `APP_PASSWORD`, add funds and expenses, pretend you will follow this regularly

## Deploy

Host-agnostic: one container + the SQLite file on a persistent disk + a backup pushed to a private git repo. For a single-user app, a free **GCP e2-micro** (or Oracle ARM, or a ~€4 Hetzner box) is plenty. See `plan.md` for the full comparison.

## Mood

Mood is generally happy, will go buy some more books today before i start tracking because they legally won't count