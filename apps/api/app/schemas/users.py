from pydantic import EmailStr, Field

from app.core.rbac import Role
from app.schemas.base import RequestModel

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
FULL_NAME_MAX_LENGTH = 150


class UserCreate(RequestModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=FULL_NAME_MAX_LENGTH)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    role: Role
