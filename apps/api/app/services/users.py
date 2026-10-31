from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.core.security import hash_password
from app.models.user import User


class DuplicateEmailError(Exception):
    """Email đã tồn tại trong hệ thống."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == normalize_email(email)))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    full_name: str,
    password: str,
    role: Role,
) -> User:
    user = User(
        email=normalize_email(email),
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateEmailError(email) from exc
    return user
