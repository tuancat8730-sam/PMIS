from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, WriteRateLimitDep
from app.core.rbac import Principal, Role, require_roles
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.users import UserCreate
from app.services.audit import record_audit
from app.services.users import DuplicateEmailError, create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: UserCreate,
    principal: Annotated[Principal, Depends(require_roles(Role.ADMIN))],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> User:
    try:
        user = await create_user(
            session,
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role=payload.role,
        )
    except DuplicateEmailError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã tồn tại trong hệ thống",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="user.create",
        entity_type="user",
        entity_id=str(user.id),
        changes={"email": user.email, "role": user.role.value},
    )
    await session.commit()
    return user
