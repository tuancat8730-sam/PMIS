from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.rbac import Role
from app.schemas.base import RequestModel


class MemberCreate(RequestModel):
    user_id: UUID
    role: Role

    @field_validator("role")
    @classmethod
    def _reject_admin(cls, value: Role) -> Role:
        # ADMIN là quyền toàn cục đã vượt qua mọi kiểm tra dự án; không gán làm thành viên.
        if value == Role.ADMIN:
            raise ValueError("Vai trò ADMIN không được gán trong dự án")
        return value


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    user_id: UUID
    role: Role
