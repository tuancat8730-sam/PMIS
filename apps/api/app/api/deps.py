import math
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.crypto import FieldCipher
from app.core.field_rules import is_valid_device_id
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.rbac import Principal, Role, get_current_principal
from app.models.contract import Contract
from app.models.project import Project
from app.services.contracts import get_contract
from app.services.field_sync import FieldWriteHeaders
from app.services.memberships import get_member_role
from app.services.projects import get_project

RATE_LIMITED_DETAIL = "Bạn thao tác quá nhiều lần, vui lòng thử lại sau"
PROJECT_NOT_FOUND_DETAIL = "Không tìm thấy dự án"
CONTRACT_NOT_FOUND_DETAIL = "Không tìm thấy hợp đồng"
PROJECT_ACCESS_DENIED_DETAIL = "Bạn không có quyền thực hiện thao tác này trong dự án"
ANY_PROJECT_ROLE: tuple[Role, ...] = tuple(Role)


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


async def get_existing_project(project_id: UUID, session: SessionDep) -> Project:
    project = await get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROJECT_NOT_FOUND_DETAIL)
    return project


ProjectDep = Annotated[Project, Depends(get_existing_project)]


async def get_existing_contract(contract_id: UUID, session: SessionDep) -> Contract:
    contract = await get_contract(session, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CONTRACT_NOT_FOUND_DETAIL)
    return contract


ContractDep = Annotated[Contract, Depends(get_existing_contract)]


def get_field_cipher(settings: SettingsDep) -> FieldCipher:
    return FieldCipher(settings.cccd_encryption_key.get_secret_value())


CipherDep = Annotated[FieldCipher, Depends(get_field_cipher)]

INVALID_DEVICE_ID_DETAIL = "X-Device-Id không hợp lệ"
INVALID_IDEMPOTENCY_KEY_DETAIL = "Idempotency-Key phải là UUID"


def get_field_write_headers(
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    device_id: Annotated[str, Header(alias="X-Device-Id")],
) -> FieldWriteHeaders:
    """Kiểm hai header của lệnh ghi từ thiết bị. Header thiếu đã được FastAPI trả 422."""
    if not is_valid_device_id(device_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=INVALID_DEVICE_ID_DETAIL,
        )
    try:
        parsed_key = UUID(idempotency_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=INVALID_IDEMPOTENCY_KEY_DETAIL,
        ) from None
    return FieldWriteHeaders(device_id=device_id, idempotency_key=parsed_key)


FieldWriteHeadersDep = Annotated[FieldWriteHeaders, Depends(get_field_write_headers)]


async def ensure_project_role(
    session: AsyncSession,
    principal: Principal,
    project_id: UUID,
    allowed: tuple[Role, ...],
) -> None:
    """ADMIN toàn cục qua mọi dự án; người khác phải là thành viên với vai trò trong `allowed`."""
    if principal.role == Role.ADMIN:
        return
    member_role = await get_member_role(session, project_id, principal.user_id)
    if member_role is None or member_role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PROJECT_ACCESS_DENIED_DETAIL,
        )


def project_role_guard(*allowed: Role) -> Callable[..., Awaitable[Project]]:
    async def _guard(
        project: ProjectDep,
        principal: Annotated[Principal, Depends(get_current_principal)],
        session: SessionDep,
    ) -> Project:
        await ensure_project_role(session, principal, project.id, allowed)
        return project

    return _guard


def contract_role_guard(*allowed: Role) -> Callable[..., Awaitable[Contract]]:
    """Kiểm quyền theo dự án của hợp đồng, dùng cho tài nguyên nằm dưới hợp đồng (nhân sự)."""

    async def _guard(
        contract: ContractDep,
        principal: Annotated[Principal, Depends(get_current_principal)],
        session: SessionDep,
    ) -> Contract:
        await ensure_project_role(session, principal, contract.project_id, allowed)
        return contract

    return _guard
