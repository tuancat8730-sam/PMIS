from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import RequestModel
from app.schemas.equipment import DeliveryStatus

VerificationStatus = Literal["ĐẠT", "KHÔNG ĐẠT"]
PhotoKind = Literal["SITE", "SIGNED_HANDOVER"]


class FieldHandoverStatusUpdate(RequestModel):
    delivery_status: DeliveryStatus
    expected_version: int = Field(ge=1)


class FieldHandoverStatusOut(BaseModel):
    id: UUID
    delivery_status: str
    version: int


class FieldSerialVerificationUpdate(RequestModel):
    verification_status: VerificationStatus
    expected_version: int = Field(ge=1)


class FieldSerialVerificationOut(BaseModel):
    id: UUID
    verification_status: str
    version: int


class FieldGpsOut(BaseModel):
    latitude: float
    longitude: float
    source: str


class FieldPhotoOut(BaseModel):
    id: UUID
    kind: str
    mime: str
    size_bytes: int
    gps: FieldGpsOut | None
    uploaded_at: datetime
