from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1 import api_router
from app.core.config import Settings, get_settings
from app.core.rate_limit import SlidingWindowRateLimiter


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)

    app = FastAPI(title="PMIS API", version="0.1.0", lifespan=_lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.login_limiter = SlidingWindowRateLimiter(
        max_hits=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    app.state.write_limiter = SlidingWindowRateLimiter(
        max_hits=settings.write_rate_limit_attempts,
        window_seconds=settings.write_rate_limit_window_seconds,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router)
    return app
