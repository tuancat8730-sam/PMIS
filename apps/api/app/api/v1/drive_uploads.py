import logging
from pathlib import PurePosixPath
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.api.deps import SessionDep, WriteRateLimitDep, project_role_guard
from app.core.drive_file_kinds import KIND_MIME_TYPES, classify_file
from app.core.drive_upload_targets import UploadKind, target_folder_path
from app.core.rbac import Principal, Role, get_current_principal
from app.integrations.drive import DriveApiError, GoogleDriveWriter
from app.integrations.drive_gateway import DriveWriter
from app.models.project import Project
from app.schemas.drive import DriveUploadOut
from app.services.audit import record_audit
from app.services.drive_upload import DriveFolderNotFoundError, upload_to_project_folder

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
DRIVE_NOT_CONFIGURED_DETAIL = "Máy chủ chưa cấu hình tài khoản dịch vụ Google Drive"
DRIVE_ROOT_NOT_CONFIGURED_DETAIL = "Dự án chưa khai báo thư mục gốc trên Google Drive"
DRIVE_FOLDER_MISSING_DETAIL = "Thiếu thư mục lưu trữ (pmis) trên Google Drive, hãy tạo trước"
UNSUPPORTED_FILE_DETAIL = "Định dạng file không được hỗ trợ"
FILE_TOO_LARGE_DETAIL = "File vượt quá 20 MB"
DRIVE_UNAVAILABLE_DETAIL = "Google Drive đang từ chối yêu cầu, hãy thử lại sau"

router = APIRouter(prefix="/projects/{project_id}/drive", tags=["drive"])


def get_drive_writer(request: Request) -> DriveWriter:
    # Ghi dùng token OAuth của người dùng: tài khoản dịch vụ không có quota trong My Drive.
    token_file_path = request.app.state.settings.drive_oauth_token_file
    if token_file_path is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=DRIVE_NOT_CONFIGURED_DETAIL
        )
    return GoogleDriveWriter.from_oauth_token_file(token_file_path)


DriveWriterDep = Annotated[DriveWriter, Depends(get_drive_writer)]


@router.post("/uploads", response_model=DriveUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_drive_file_endpoint(
    project_id: UUID,
    project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    writer: DriveWriterDep,
    _rate_limit: WriteRateLimitDep,
    kind: Annotated[UploadKind, Form()],
    file: Annotated[UploadFile, File()],
) -> DriveUploadOut:
    file_name = PurePosixPath(file.filename or "").name
    file_kind = classify_file(file_name)
    if file_kind is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=UNSUPPORTED_FILE_DETAIL
        )
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=FILE_TOO_LARGE_DETAIL
        )
    if project.drive_root_folder_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DRIVE_ROOT_NOT_CONFIGURED_DETAIL
        )

    try:
        result = upload_to_project_folder(
            writer,
            project.drive_root_folder_id,
            target_folder_path(kind),
            file_name,
            content,
            KIND_MIME_TYPES[file_kind],
        )
    except DriveFolderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DRIVE_FOLDER_MISSING_DETAIL
        ) from None
    except DriveApiError as error:
        logger.error("Đẩy file lên Drive thất bại: project=%s status=%s", project_id, error.status)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=DRIVE_UNAVAILABLE_DETAIL
        ) from None

    output = DriveUploadOut(file_id=result.file_id, created=result.created)
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="drive.upload",
        entity_type="project",
        entity_id=str(project_id),
        changes={"kind": kind.value, "file_name": file_name, "created": result.created},
    )
    await session.commit()
    return output
