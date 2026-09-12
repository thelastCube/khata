"""Single-user auth: a signed, timed session cookie."""
from fastapi import Depends, HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import Settings, get_settings


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt="session")


def create_session_token(settings: Settings) -> str:
    return _serializer(settings).dumps({"u": "owner"})


def require_auth(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        _serializer(settings).loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
