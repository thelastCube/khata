"""Profile (user) management: create/list/delete profiles, authenticate,
change/reset passwords, set avatars, and seed the default admin.

Admin actions here only ever touch the auth DB (and delete a profile's data
file) — they never open another profile's data, so 'accounts only' isolation
holds by construction."""
from ..config import Settings
from ..dao.users_dao import UsersDao
from ..db import profile_db_path
from ..models import User
from ..security import hash_password, verify_password
from ..util import now_iso

DEFAULT_ADMIN_NAME = "Chai"
DEFAULT_ADMIN_AVATAR = "🐸"
MAX_AVATAR_LEN = 300_000  # ~225 KB as a data URI


class UserError(ValueError):
    pass


def _clean_avatar(avatar: str | None) -> str | None:
    if not avatar:
        return None
    avatar = avatar.strip()
    if len(avatar) > MAX_AVATAR_LEN:
        raise UserError("avatar image is too large")
    if avatar.startswith("data:image/") or len(avatar) <= 16:  # image, or an emoji
        return avatar
    raise UserError("avatar must be an emoji or an image")


class UserService:
    def __init__(self, users: UsersDao, settings: Settings):
        self.users = users
        self.settings = settings

    # --- reads ---
    def list_profiles(self) -> list[dict]:
        """Public picker data — no hashes, no admin flags."""
        return [{"id": u.id, "name": u.name, "avatar": u.avatar} for u in self.users.list()]

    def list_users(self) -> list[User]:
        return self.users.list()

    def get(self, user_id: int) -> User:
        u = self.users.get(user_id)
        if not u:
            raise UserError(f"profile {user_id} not found")
        return u

    # --- auth ---
    def authenticate(self, user_id: int, password: str) -> User | None:
        u = self.users.get(user_id)
        if u and verify_password(password, u.password_hash):
            return u
        return None

    # --- admin: create / delete / reset ---
    def create(self, name: str, password: str, avatar: str | None, is_admin: bool) -> User:
        name = (name or "").strip()
        if not name:
            raise UserError("name is required")
        if not password:
            raise UserError("password is required")
        if self.users.get_by_name(name):
            raise UserError(f"profile '{name}' already exists")
        u = User(name=name, avatar=_clean_avatar(avatar), password_hash=hash_password(password),
                 is_admin=is_admin, must_change_password=True, created_at=now_iso())
        return self.users.create(u)

    def delete(self, user_id: int, acting_user_id: int) -> None:
        if user_id == acting_user_id:
            raise UserError("you can't delete your own profile")
        u = self.get(user_id)
        if u.is_admin and self.users.count_admins() <= 1:
            raise UserError("can't delete the last admin")
        self.users.delete(user_id)
        # remove the profile's data file(s)
        base = profile_db_path(self.settings, user_id)
        for suffix in ("", "-wal", "-shm"):
            p = base.parent / (base.name + suffix)
            if p.exists():
                p.unlink()

    def admin_reset_password(self, user_id: int, new_password: str) -> None:
        if not new_password:
            raise UserError("password is required")
        self.get(user_id)
        self.users.set_password(user_id, hash_password(new_password), must_change=True)

    # --- self service ---
    def change_password(self, user_id: int, current: str, new: str) -> None:
        u = self.get(user_id)
        if not verify_password(current, u.password_hash):
            raise UserError("current password is wrong")
        if not new:
            raise UserError("new password is required")
        self.users.set_password(user_id, hash_password(new), must_change=False)

    def set_avatar(self, user_id: int, avatar: str | None) -> None:
        self.get(user_id)
        self.users.set_avatar(user_id, _clean_avatar(avatar))


def seed_default_admin(settings: Settings) -> None:
    """Create Chai (🐸, admin) if there are no profiles yet. Idempotent."""
    from ..auth_db import connect_auth
    conn = connect_auth(settings)
    try:
        dao = UsersDao(conn)
        if dao.count() == 0:
            dao.create(User(
                name=DEFAULT_ADMIN_NAME, avatar=DEFAULT_ADMIN_AVATAR,
                password_hash=hash_password(settings.app_password),
                is_admin=True, must_change_password=True, created_at=now_iso()))
            conn.commit()
    finally:
        conn.close()
