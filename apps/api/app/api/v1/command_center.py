from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep
from app.core.rbac import Principal, Role, get_current_principal
from app.schemas.command_center import CommandCenterOut
from app.services.command_center import build_command_center

router = APIRouter(prefix="/command-center", tags=["command-center"])


@router.get("", response_model=CommandCenterOut)
async def get_command_center(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
) -> CommandCenterOut:
    """Chỉ đọc. ADMIN thấy mọi dự án, các vai trò khác chỉ thấy dự án mình là thành viên."""
    member_user_id = None if principal.role == Role.ADMIN else principal.user_id
    return await build_command_center(
        session,
        today=datetime.now(UTC).date(),
        member_user_id=member_user_id,
    )
