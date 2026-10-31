from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services.users import get_user_by_email

# Băm giả để thời gian phản hồi khi email không tồn tại không lộ việc tài khoản có hay không.
_DUMMY_HASH = hash_password("khong-phai-mat-khau-that")


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    password_ok = verify_password(password, user.hashed_password)
    if not password_ok or not user.is_active:
        return None
    return user
