from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schedule_rules import missing_confirmation_parties
from app.models.hold_point import ConfirmingParty, HoldPoint
from app.schemas.base import RequestModel
from app.services.hold_points import REQUIRED_PARTIES

HOLD_POINT_NAME_MAX_LENGTH = 300
HOLD_POINT_CODE_PATTERN = r"^H[0-9]$"
EVIDENCE_REF_MAX_LENGTH = 500


class HoldPointCreate(RequestModel):
    code: str = Field(pattern=HOLD_POINT_CODE_PATTERN)
    name: str = Field(min_length=1, max_length=HOLD_POINT_NAME_MAX_LENGTH)
    milestone_id: UUID | None = None


class ConfirmationCreate(RequestModel):
    party: ConfirmingParty
    evidence_ref: str = Field(min_length=1, max_length=EVIDENCE_REF_MAX_LENGTH)


class HoldPointOut(BaseModel):
    id: UUID
    project_id: UUID
    milestone_id: UUID | None
    code: str
    name: str
    confirmed_parties: list[str]
    missing_parties: list[str]
    cleared: bool

    @classmethod
    def from_hold_point(cls, hold_point: HoldPoint, confirmed: set[str]) -> "HoldPointOut":
        missing = sorted(missing_confirmation_parties(confirmed, REQUIRED_PARTIES))
        return cls(
            id=hold_point.id,
            project_id=hold_point.project_id,
            milestone_id=hold_point.milestone_id,
            code=hold_point.code,
            name=hold_point.name,
            confirmed_parties=sorted(confirmed),
            missing_parties=missing,
            cleared=not missing,
        )
