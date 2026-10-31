from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.contract_personnel import PersonnelComplianceStatus
from app.schemas.base import RequestModel

FULL_NAME_MAX_LENGTH = 150
ORGANIZATION_MAX_LENGTH = 150
POSITION_ROLE_MAX_LENGTH = 200
CCCD_PATTERN = r"^\d{12}$"


class PersonnelCreate(RequestModel):
    full_name: str = Field(min_length=1, max_length=FULL_NAME_MAX_LENGTH)
    organization: str | None = Field(default=None, max_length=ORGANIZATION_MAX_LENGTH)
    position_role: str = Field(min_length=1, max_length=POSITION_ROLE_MAX_LENGTH)
    national_id_cccd: str | None = Field(default=None, pattern=CCCD_PATTERN)
    qualification: str | None = None
    is_backup_staff: bool = False

    @field_validator("national_id_cccd", mode="before")
    @classmethod
    def _strip_spaces(cls, value: Any) -> Any:
        # Người nhập hay gõ CCCD có khoảng trắng; bỏ đi trước khi kiểm định dạng.
        if isinstance(value, str):
            return value.replace(" ", "")
        return value


class PersonnelOut(BaseModel):
    """Nhân sự trả về client. CCCD chỉ hiện 4 số cuối, không bao giờ trả bản đầy đủ."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contract_id: UUID
    full_name: str
    organization: str | None
    position_role: str
    national_id_masked: str | None
    qualification: str | None
    is_backup_staff: bool
    compliance_status: PersonnelComplianceStatus
