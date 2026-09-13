"""SQL for the users (profiles) table in the auth DB."""
import sqlite3

from ..models import User


class UsersDao:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _row(r: sqlite3.Row) -> User:
        return User(
            id=r["id"], name=r["name"], avatar=r["avatar"], password_hash=r["password_hash"],
            is_admin=bool(r["is_admin"]), must_change_password=bool(r["must_change_password"]),
            created_at=r["created_at"],
        )

    def create(self, u: User) -> User:
        cur = self.conn.execute(
            """INSERT INTO users(name, avatar, password_hash, is_admin, must_change_password, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (u.name, u.avatar, u.password_hash, int(u.is_admin), int(u.must_change_password), u.created_at),
        )
        u.id = cur.lastrowid
        return u

    def get(self, user_id: int) -> User | None:
        r = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row(r) if r else None

    def get_by_name(self, name: str) -> User | None:
        r = self.conn.execute("SELECT * FROM users WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return self._row(r) if r else None

    def list(self) -> list[User]:
        return [self._row(r) for r in self.conn.execute("SELECT * FROM users ORDER BY id").fetchall()]

    def update(self, user_id: int, name: str, avatar: str | None,
               is_admin: bool, must_change_password: bool) -> None:
        self.conn.execute(
            "UPDATE users SET name = ?, avatar = ?, is_admin = ?, must_change_password = ? WHERE id = ?",
            (name, avatar, int(is_admin), int(must_change_password), user_id),
        )

    def set_avatar(self, user_id: int, avatar: str | None) -> None:
        self.conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))

    def set_password(self, user_id: int, password_hash: str, must_change: bool) -> None:
        self.conn.execute(
            "UPDATE users SET password_hash = ?, must_change_password = ? WHERE id = ?",
            (password_hash, int(must_change), user_id),
        )

    def delete(self, user_id: int) -> None:
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"])

    def count_admins(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin = 1").fetchone()["c"])
