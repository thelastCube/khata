"""Profile routes: the public picker list, whoami, self-service (password +
avatar), and admin-only profile management."""
from fastapi import APIRouter, Depends

from ..auth import current_user, require_admin
from ..deps import user_service
from ..models import User
from ..schemas import (AvatarIn, CreateUserIn, MessageResponse, PasswordChangeIn,
                       ProfileOut, ResetPasswordIn, UserOut, WhoAmI)
from ..services.user_service import UserService

router = APIRouter(tags=["profiles"])


def _out(u: User) -> UserOut:
    return UserOut(id=u.id, name=u.name, avatar=u.avatar, is_admin=u.is_admin,
                   must_change_password=u.must_change_password, created_at=u.created_at)


# --- public: the login picker ---
@router.get("/profiles", response_model=list[ProfileOut])
def profiles(svc: UserService = Depends(user_service)):
    return [ProfileOut(**p) for p in svc.list_profiles()]


# --- current session ---
@router.get("/whoami", response_model=WhoAmI)
def whoami(user: User = Depends(current_user)):
    return WhoAmI(id=user.id, name=user.name, avatar=user.avatar,
                  is_admin=user.is_admin, must_change_password=user.must_change_password)


@router.post("/me/password", response_model=MessageResponse)
def change_password(body: PasswordChangeIn, user: User = Depends(current_user),
                    svc: UserService = Depends(user_service)):
    svc.change_password(user.id, body.current_password, body.new_password)
    return MessageResponse(message="password changed")


@router.put("/me/avatar", response_model=MessageResponse)
def set_avatar(body: AvatarIn, user: User = Depends(current_user),
               svc: UserService = Depends(user_service)):
    svc.set_avatar(user.id, body.avatar)
    return MessageResponse(message="avatar updated")


# --- admin only ---
@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), svc: UserService = Depends(user_service)):
    return [_out(u) for u in svc.list_users()]


@router.post("/users", response_model=UserOut)
def create_user(body: CreateUserIn, _: User = Depends(require_admin),
                svc: UserService = Depends(user_service)):
    return _out(svc.create(body.name, body.password, body.avatar, body.is_admin))


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
def reset_password(user_id: int, body: ResetPasswordIn, _: User = Depends(require_admin),
                   svc: UserService = Depends(user_service)):
    svc.admin_reset_password(user_id, body.new_password)
    return MessageResponse(message="password reset")


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(user_id: int, actor: User = Depends(require_admin),
                svc: UserService = Depends(user_service)):
    svc.delete(user_id, actor.id)
    return MessageResponse(message="deleted")
