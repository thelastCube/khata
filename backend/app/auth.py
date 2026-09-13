"""Session auth: a signed, timed cookie carrying the profile id, plus the
dependencies that resolve it to a user and gate admin-only routes.

This module must not import `db` (db imports `current_user` from here)."""
import sqlite3

from fastapi import Depends, HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .auth_db import get_auth_db
from .config import Settings, get_settings
from .dao.users_dao import UsersDao
from .models import User


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt="session")


def create_session_token(settings: Settings, user_id: int) -> str:
    return _serializer(settings).dumps({"uid": user_id})


def require_auth(request: Request, settings: Settings = Depends(get_settings)) -> int:
    """Validate the cookie and return the profile id it carries."""
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        data = _serializer(settings).loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    uid = data.get("uid")
    if not isinstance(uid, int):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")
    return uid


def current_user(
    uid: int = Depends(require_auth),
    auth_conn: sqlite3.Connection = Depends(get_auth_db),
) -> User:
    user = UsersDao(auth_conn).get(uid)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Profile no longer exists")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
