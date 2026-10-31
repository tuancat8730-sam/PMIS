import math
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.rate_limit import SlidingWindowRateLimiter

RATE_LIMITED_DETAIL = "Bạn thao tác quá nhiều lần, vui lòng thử lại sau"


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def _enforce_rate_limit(limiter: SlidingWindowRateLimiter, request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    wait_seconds = limiter.acquire(client_ip)
    if wait_seconds > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMITED_DETAIL,
            headers={"Retry-After": str(math.ceil(wait_seconds))},
        )


# async để chạy trên event loop; bộ đếm không có khóa nên không được chạy trên thread pool.
async def limit_login(request: Request) -> None:
    _enforce_rate_limit(request.app.state.login_limiter, request)


async def limit_writes(request: Request) -> None:
    _enforce_rate_limit(request.app.state.write_limiter, request)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
LoginRateLimitDep = Annotated[None, Depends(limit_login)]
WriteRateLimitDep = Annotated[None, Depends(limit_writes)]
