from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.project_file_register import (
    FILE_FORMAT_MAX_LENGTH,
    SECURITY_OWNERSHIP_MAX_LENGTH,
    STORAGE_LOCATION_MAX_LENGTH,
)
from app.schemas.base import RequestModel

FOLDER_PATH_MAX_LENGTH = 1000
FILE_NAME_MAX_LENGTH = 1000
TEXT_MAX_LENGTH = 4000


class FileRegisterCreate(RequestModel):
    stt: int = Field(ge=1)
    folder_path: str | None = Field(default=None, max_length=FOLDER_PATH_MAX_LENGTH)
    file_name: str = Field(min_length=1, max_length=FILE_NAME_MAX_LENGTH)
    file_format: str | None = Field(default=None, max_length=FILE_FORMAT_MAX_LENGTH)
    storage_location: str | None = Field(default=None, max_length=STORAGE_LOCATION_MAX_LENGTH)
    purpose: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    legal_status: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    security_ownership: str | None = Field(default=None, max_length=SECURITY_OWNERSHIP_MAX_LENGTH)
    next_action: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    drive_file_id: UUID | None = None


class FileRegisterUpdate(RequestModel):
    """Sửa dòng register. `stt` không đổi sau khi tạo để giữ thứ tự đối chiếu với báo cáo."""

    folder_path: str | None = Field(default=None, max_length=FOLDER_PATH_MAX_LENGTH)
    file_name: str | None = Field(default=None, min_length=1, max_length=FILE_NAME_MAX_LENGTH)
    file_format: str | None = Field(default=None, max_length=FILE_FORMAT_MAX_LENGTH)
    storage_location: str | None = Field(default=None, max_length=STORAGE_LOCATION_MAX_LENGTH)
    purpose: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    legal_status: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    security_ownership: str | None = Field(default=None, max_length=SECURITY_OWNERSHIP_MAX_LENGTH)
    next_action: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    drive_file_id: UUID | None = None

    @model_validator(mode="after")
    def _reject_null_for_file_name(self) -> "FileRegisterUpdate":
        if "file_name" in self.model_fields_set and self.file_name is None:
            raise ValueError("file_name không được để trống")
        return self


class FileRegisterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    stt: int
    folder_path: str | None
    file_name: str
    file_format: str | None
    storage_location: str | None
    purpose: str | None
    legal_status: str | None
    security_ownership: str | None
    next_action: str | None
    drive_file_id: UUID | None
