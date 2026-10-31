from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.beneficiary_unit import (
    CLUSTER_CODE_MAX_LENGTH,
    PERSON_NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    PROVINCE_MAX_LENGTH,
    ROLE_MAX_LENGTH,
    UNIT_CODE_MAX_LENGTH,
    ReadinessStatus,
    UnitType,
)
from app.schemas.base import RequestModel
from app.services.beneficiary_units import display_dual_name

OFFICIAL_NAME_MAX_LENGTH = 300
FORMER_NAME_MAX_LENGTH = 300
CLUSTER_NAME_MAX_LENGTH = 300
ADDRESS_MAX_LENGTH = 500
DISTRICT_MAX_LENGTH = 300
UNIT_CODE_PATTERN = r"^\S+$"


class BeneficiaryUnitCreate(RequestModel):
    unit_code: str = Field(
        min_length=1,
        max_length=UNIT_CODE_MAX_LENGTH,
        pattern=UNIT_CODE_PATTERN,
    )
    official_name: str = Field(min_length=1, max_length=OFFICIAL_NAME_MAX_LENGTH)
    former_name: str | None = Field(default=None, max_length=FORMER_NAME_MAX_LENGTH)
    unit_type: UnitType
    cluster_code: str = Field(min_length=1, max_length=CLUSTER_CODE_MAX_LENGTH)
    cluster_name: str | None = Field(default=None, max_length=CLUSTER_NAME_MAX_LENGTH)
    district_or_commune: str | None = Field(default=None, max_length=DISTRICT_MAX_LENGTH)
    former_province: str | None = Field(default=None, max_length=PROVINCE_MAX_LENGTH)
    address: str | None = Field(default=None, max_length=ADDRESS_MAX_LENGTH)
    principal_name: str | None = Field(default=None, max_length=PERSON_NAME_MAX_LENGTH)
    focal_point_name: str | None = Field(default=None, max_length=PERSON_NAME_MAX_LENGTH)
    focal_point_role: str | None = Field(default=None, max_length=ROLE_MAX_LENGTH)
    focal_point_phone: str | None = Field(default=None, max_length=PHONE_MAX_LENGTH)


class BeneficiaryUnitUpdate(RequestModel):
    """Mã đơn vị là khóa nghiệp vụ nên không cho sửa; mọi trường khác là tùy chọn."""

    official_name: str | None = Field(
        default=None, min_length=1, max_length=OFFICIAL_NAME_MAX_LENGTH
    )
    former_name: str | None = Field(default=None, max_length=FORMER_NAME_MAX_LENGTH)
    unit_type: UnitType | None = None
    cluster_code: str | None = Field(default=None, min_length=1, max_length=CLUSTER_CODE_MAX_LENGTH)
    cluster_name: str | None = Field(default=None, max_length=CLUSTER_NAME_MAX_LENGTH)
    district_or_commune: str | None = Field(default=None, max_length=DISTRICT_MAX_LENGTH)
    former_province: str | None = Field(default=None, max_length=PROVINCE_MAX_LENGTH)
    address: str | None = Field(default=None, max_length=ADDRESS_MAX_LENGTH)
    principal_name: str | None = Field(default=None, max_length=PERSON_NAME_MAX_LENGTH)
    focal_point_name: str | None = Field(default=None, max_length=PERSON_NAME_MAX_LENGTH)
    focal_point_role: str | None = Field(default=None, max_length=ROLE_MAX_LENGTH)
    focal_point_phone: str | None = Field(default=None, max_length=PHONE_MAX_LENGTH)
    readiness_status: ReadinessStatus | None = None


class BeneficiaryUnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    unit_code: str
    official_name: str
    former_name: str | None
    unit_type: UnitType
    cluster_code: str
    cluster_name: str | None
    district_or_commune: str | None
    former_province: str | None
    address: str | None
    principal_name: str | None
    focal_point_name: str | None
    focal_point_role: str | None
    focal_point_phone: str | None
    readiness_status: ReadinessStatus

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_dual_name(self) -> str:
        return display_dual_name(self.official_name, self.former_name)
