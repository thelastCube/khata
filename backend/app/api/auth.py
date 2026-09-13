"""Auth routes: login (profile id + password) sets the session cookie."""
from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..auth import create_session_token
from ..config import Settings, get_settings
from ..deps import user_service
from ..schemas import LoginRequest, MessageResponse
from ..services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MessageResponse)
def login(
    body: LoginRequest,
    response: Response,
    svc: UserService = Depends(user_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    user = svc.authenticate(body.user_id, body.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong password")
    response.set_cookie(
        settings.cookie_name,
        create_session_token(settings, user.id),
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
    )
    return MessageResponse(message="logged in")


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, settings: Settings = Depends(get_settings)) -> MessageResponse:
    response.delete_cookie(settings.cookie_name)
    return MessageResponse(message="logged out")
