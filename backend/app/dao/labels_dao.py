"""SQL for labels and label-groups."""
import sqlite3

from ..models import Label


class LabelsDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _row(r: sqlite3.Row) -> Label:
        return Label(id=r["id"], name=r["name"], color=r["color"])

    # --- labels ---
    def create(self, label: Label) -> Label:
        cur = self.conn.execute(
            "INSERT INTO labels(name, color) VALUES (?, ?)", (label.name, label.color)
        )
        label.id = cur.lastrowid
        return label

    def get(self, label_id: int) -> Label | None:
        r = self.conn.execute("SELECT * FROM labels WHERE id = ?", (label_id,)).fetchone()
        return self._row(r) if r else None

    def get_by_name(self, name: str) -> Label | None:
        # case-insensitive match; stored name keeps its original case
        r = self.conn.execute("SELECT * FROM labels WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return self._row(r) if r else None

    def list(self) -> list[Label]:
        return [self._row(r) for r in self.conn.execute("SELECT * FROM labels ORDER BY name").fetchall()]

    def update(self, label: Label) -> Label:
        self.conn.execute(
            "UPDATE labels SET name = ?, color = ? WHERE id = ?",
            (label.name, label.color, label.id),
        )
        return label

    def delete(self, label_id: int) -> None:
        self.conn.execute("DELETE FROM labels WHERE id = ?", (label_id,))

    # --- groups ---
    def create_group(self, name: str) -> int:
        cur = self.conn.execute("INSERT INTO label_groups(name) VALUES (?)", (name,))
        return cur.lastrowid

    def get_group(self, group_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM label_groups WHERE id = ?", (group_id,)).fetchone()

    def list_groups(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM label_groups ORDER BY name").fetchall()

    def rename_group(self, group_id: int, name: str) -> None:
        self.conn.execute("UPDATE label_groups SET name = ? WHERE id = ?", (name, group_id))

    def delete_group(self, group_id: int) -> None:
        self.conn.execute("DELETE FROM label_groups WHERE id = ?", (group_id,))

    def set_group_labels(self, group_id: int, label_ids: list[int]) -> None:
        self.conn.execute("DELETE FROM group_labels WHERE group_id = ?", (group_id,))
        self.conn.executemany(
            "INSERT INTO group_labels(group_id, label_id) VALUES (?, ?)",
            [(group_id, lid) for lid in label_ids],
        )

    def group_label_ids(self, group_id: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT label_id FROM group_labels WHERE group_id = ?", (group_id,)
        ).fetchall()
        return [r["label_id"] for r in rows]
