from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import LoginRateLimitDep, SessionDep, SettingsDep
from app.core.rbac import Principal, get_current_principal
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import TokenOut, UserOut
from app.services.audit import record_audit
from app.services.auth import authenticate

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID_CREDENTIALS_DETAIL = "Email hoặc mật khẩu không đúng"
SESSION_INVALID_DETAIL = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
ACTION_LOGIN = "auth.login"
ACTION_LOGIN_FAILED = "auth.login_failed"


@router.post("/login", response_model=TokenOut)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    settings: SettingsDep,
    _rate_limit: LoginRateLimitDep,
) -> TokenOut:
    user = await authenticate(session, email=form.username, password=form.password)
    if user is None:
        await record_audit(
            session,
            actor_id=None,
            action=ACTION_LOGIN_FAILED,
            entity_type="user",
            changes={"email": form.username},
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )

    await record_audit(
        session,
        actor_id=user.id,
        action=ACTION_LOGIN,
        entity_type="user",
        entity_id=str(user.id),
    )
    await session.commit()
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        secret=settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        expires_in=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenOut(access_token=token, role=user.role)


@router.get("/me", response_model=UserOut)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
) -> User:
    user = await session.get(User, principal.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=SESSION_INVALID_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
