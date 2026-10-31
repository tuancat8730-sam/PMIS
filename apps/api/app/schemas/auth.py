from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.rbac import Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class UserOut(BaseModel):
    """Thông tin người dùng trả về client. Tuyệt đối không chứa hash mật khẩu."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
