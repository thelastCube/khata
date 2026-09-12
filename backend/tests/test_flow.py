"""End-to-end flow across funds, labels, expenses, budgets, overview,
siphon transfers, the carryover engine, analysis, audit, and backup."""

MONTH = "2026-09"
NEXT = "2026-10"
NEXT2 = "2026-11"


def test_full_flow(auth_client):
    c = auth_client

    food = c.post("/funds", json={"name": "Food"}).json()
    hobby = c.post("/funds", json={"name": "Hobbies"}).json()
    travel = c.post("/funds", json={"name": "Travel"}).json()

    # Budgets: Food overspends (repay over 2 months), Hobbies rolls leftover forward.
    c.put(f"/budgets/{food['id']}?month={MONTH}",
          json={"amount": 5000, "carry_overspend": True, "emi_months": 2})
    c.put(f"/budgets/{hobby['id']}?month={MONTH}",
          json={"amount": 3000, "carry_underspend": True})
    c.put(f"/budgets/{travel['id']}?month={MONTH}",
          json={"amount": 1000, "carry_overspend": True, "emi_months": 2})

    # Expenses (labels created on the fly).
    c.post("/expenses", json={"amount": 6000, "fund_id": food["id"],
                              "labels": ["groceries", "friend"], "ts": f"{MONTH}-10T12:00:00"})
    c.post("/expenses", json={"amount": 1000, "fund_id": hobby["id"],
                              "labels": ["books"], "ts": f"{MONTH}-11T12:00:00"})
    c.post("/expenses", json={"amount": 3000, "fund_id": travel["id"],
                              "labels": [], "ts": f"{MONTH}-05T12:00:00"})

    # Overview: Food is over by 1000 and sorts first (most exceeded).
    ov = c.get(f"/overview?month={MONTH}").json()
    food_row = next(r for r in ov if r["fund"]["id"] == food["id"])
    assert food_row["spent"] == 6000 and food_row["overage"] == 1000
    assert ov[0]["overage"] >= ov[-1]["overage"]

    # Balance suggestions: Hobbies has 2000 spare.
    sug = c.get(f"/funds/{food['id']}/balance-suggestions?month={MONTH}").json()
    assert any(s["fund"]["id"] == hobby["id"] and s["surplus"] == 2000 for s in sug)

    # Siphon 1000 Hobbies -> Food; Food's overage clears.
    assert c.post("/transfers", json={"month": MONTH, "from_fund_id": hobby["id"],
                                      "to_fund_id": food["id"], "amount": 1000,
                                      "reason": "cover food"}).status_code == 200
    detail = c.get(f"/funds/{food['id']}/detail?month={MONTH}").json()
    assert detail["overage"] == 0 and detail["available"] == 6000
    assert detail["delta_vs_prev"] == 6000  # no spend last month

    # Over-siphon is rejected.
    assert c.post("/transfers", json={"month": MONTH, "from_fund_id": hobby["id"],
                                      "to_fund_id": food["id"], "amount": 9999}).status_code == 400

    # Analysis: spend tagged 'friend' this month.
    labels = {label["name"]: label["id"] for label in c.get("/labels").json()}
    an = c.get(f"/analysis?month={MONTH}&label_ids={labels['friend']}").json()
    assert an["total"] == 6000 and an["count"] == 1

    # Close the month: Travel repays 2000 over 2 months; Hobbies rolls 1000 forward.
    c.post(f"/months/{MONTH}/close")
    assert c.get(f"/funds/{travel['id']}/detail?month={NEXT}").json()["carry"] == -1000
    assert c.get(f"/funds/{travel['id']}/detail?month={NEXT2}").json()["carry"] == -1000
    assert c.get(f"/funds/{hobby['id']}/detail?month={NEXT}").json()["carry"] == 1000

    # Re-closing is idempotent (no doubling).
    c.post(f"/months/{MONTH}/close")
    assert c.get(f"/funds/{travel['id']}/detail?month={NEXT}").json()["carry"] == -1000

    # Audit trail + CSV backup.
    actions = [a["action"] for a in c.get("/audit").json()]
    assert "month.close" in actions and "transfer.create" in actions and "expense.create" in actions
    assert c.post("/backup/export").json()["rows"]["funds"] == 3


def test_fund_with_expenses_is_deactivated_not_deleted(auth_client):
    c = auth_client
    f = c.post("/funds", json={"name": "Rent"}).json()
    c.post("/expenses", json={"amount": 100, "fund_id": f["id"], "labels": []})
    assert c.delete(f"/funds/{f['id']}").json()["message"] == "deactivated"
    assert c.get(f"/funds/{f['id']}").json()["active"] is False


def test_duplicate_fund_name_rejected(auth_client):
    c = auth_client
    assert c.post("/funds", json={"name": "Food"}).status_code == 200
    assert c.post("/funds", json={"name": "Food"}).status_code == 400


def test_case_insensitive_and_deduped_labels(auth_client):
    c = auth_client
    f = c.post("/funds", json={"name": "Misc"}).json()
    c.post("/labels", json={"name": "Coffee"})
    before = len(c.get("/labels").json())
    e = c.post("/expenses", json={"amount": 100, "fund_id": f["id"], "labels": ["coffee", "COFFEE", "Coffee"]})
    assert e.status_code == 200
    assert len(e.json()["label_ids"]) == 1               # all collapse to one
    assert len(c.get("/labels").json()) == before        # reused, none created


def test_fund_default_budget_applies_without_override(auth_client):
    c = auth_client
    f = c.post("/funds", json={"name": "Rent", "default_amount": 15000}).json()
    b = c.get(f"/budgets/{f['id']}?month=2026-09").json()
    assert b["amount"] == 15000 and b["is_override"] is False
    c.put(f"/budgets/{f['id']}?month=2026-09", json={"amount": 18000})   # override one month
    assert c.get(f"/budgets/{f['id']}?month=2026-09").json()["is_override"] is True
    c.request("DELETE", f"/budgets/{f['id']}?month=2026-09")             # revert
    assert c.get(f"/budgets/{f['id']}?month=2026-09").json()["amount"] == 15000
