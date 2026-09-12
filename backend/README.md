# khata — backend

## Run (localhost)

```bash
cd backend
python -m venv amogus && source amogus/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # then edit APP_PASSWORD + SECRET_KEY

uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Test

```bash
pytest
```

## Seed mock data

```bash
python seed.py    # wipes the DB, loads a demo current + previous month
```