"""Cross-cutting analysis: total spend for any combination of labels
(AND semantics) optionally within a group, month, or fund, with a
breakdown by fund and by label."""
from collections import defaultdict

from ..dao.expenses_dao import ExpensesDao
from ..dao.funds_dao import FundsDao
from ..dao.labels_dao import LabelsDao


class AnalysisService:
    def __init__(self, expenses: ExpensesDao, funds: FundsDao, labels: LabelsDao):
        self.expenses = expenses
        self.funds = funds
        self.labels = labels

    def summarize(self, months: list[str] | None = None, fund_id: int | None = None,
                  label_ids: list[int] | None = None, group_id: int | None = None) -> dict:
        ids = list(label_ids or [])
        if group_id is not None:
            ids.extend(self.labels.group_label_ids(group_id))
        ids = sorted(set(ids)) or None

        matches = self.expenses.list(months=months, fund_id=fund_id, label_ids=ids)
        total = sum(e.amount for e in matches)

        by_fund: dict[int, float] = defaultdict(float)
        by_label: dict[int, float] = defaultdict(float)
        for e in matches:
            by_fund[e.fund_id] += e.amount
            for lid in e.label_ids:
                by_label[lid] += e.amount

        fund_names = {f.id: f.name for f in self.funds.list(include_inactive=True)}
        label_names = {label.id: label.name for label in self.labels.list()}

        return {
            "filters": {"months": months, "fund_id": fund_id, "label_ids": ids, "group_id": group_id},
            "total": total,
            "count": len(matches),
            "by_fund": [{"fund_id": k, "name": fund_names.get(k, "?"), "total": v}
                        for k, v in sorted(by_fund.items(), key=lambda x: -x[1])],
            "by_label": [{"label_id": k, "name": label_names.get(k, "?"), "total": v}
                         for k, v in sorted(by_label.items(), key=lambda x: -x[1])],
            "expenses": [{"id": e.id, "ts": e.ts, "amount": e.amount, "fund_id": e.fund_id,
                          "note": e.note, "label_ids": e.label_ids} for e in matches],
        }
