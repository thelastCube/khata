"""Small pure helpers (no I/O, no SQL)."""
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def month_of(ts: str) -> str:
    """'2026-09-11T20:00:00' -> '2026-09'."""
    return ts[:7]


def add_months(month: str, k: int) -> str:
    """'2026-09' + 1 -> '2026-10'; handles year rollover and negatives."""
    year, mon = (int(x) for x in month.split("-"))
    idx = year * 12 + (mon - 1) + k
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"
