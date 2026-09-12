"""Auth routes: login sets the session cookie, logout clears it."""
import hmac

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..auth import create_session_token
from ..config import Settings, get_settings
from ..schemas import LoginRequest, MessageResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MessageResponse)
def login(
    body: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    if not hmac.compare_digest(body.password, settings.app_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong password")
    response.set_cookie(
        settings.cookie_name,
        create_session_token(settings),
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
    )
    return MessageResponse(message="logged in")


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    response.delete_cookie(settings.cookie_name)
    return MessageResponse(message="logged out")
