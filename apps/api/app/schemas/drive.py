from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DriveFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    drive_file_id: str
    drive_path: str | None
    file_name: str
    mime_type: str | None
    file_size: int | None
    web_view_link: str | None
    modified_time: datetime | None
    last_synced_at: datetime


class DriveSyncOut(BaseModel):
    scanned: int
    created: int
    updated: int


class DriveUploadOut(BaseModel):
    file_id: str
    created: bool


class DriveMatchSuggestionOut(BaseModel):
    drive_file_id: str
    document_id: UUID
    reason: str
