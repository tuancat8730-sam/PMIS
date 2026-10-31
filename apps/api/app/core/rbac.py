from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings
from app.core.security import decode_access_token

LOGIN_PATH = "/api/v1/auth/login"
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=LOGIN_PATH)


class Role(StrEnum):
    ADMIN = "ADMIN"
    PM = "PM"
    PM_CONSULTANT = "PM_CONSULTANT"
    SUPERVISION_CONSULTANT = "SUPERVISION_CONSULTANT"
    INVESTOR = "INVESTOR"
    CONTRACTOR = "CONTRACTOR"
    FIELD_ENGINEER = "FIELD_ENGINEER"


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    role: Role


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_principal(
    request: Request,
    token: str = Depends(_oauth2_scheme),
) -> Principal:
    settings: Settings = request.app.state.settings
    try:
        claims = decode_access_token(
            token,
            secret=settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )
        return Principal(user_id=UUID(claims.subject), role=Role(claims.role))
    except (jwt.InvalidTokenError, ValueError):
        raise _unauthorized("Phiên đăng nhập không hợp lệ hoặc đã hết hạn") from None


def require_roles(*allowed: Role) -> Callable[..., Principal]:
    def _check(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này",
            )
        return principal

    return _check
