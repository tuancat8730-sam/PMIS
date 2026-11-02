import logging
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, project_role_guard
from app.api.v1.drive import DRIVE_UNAVAILABLE_DETAIL, DriveGatewayDep
from app.core.drive_preview_rules import DrivePreviewNotAllowedError, DrivePreviewTooLargeError
from app.integrations.drive import DriveApiError
from app.models.project import Project
from app.services.drive_content import DriveFileNotFoundError, load_drive_file_preview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/drive", tags=["drive"])

NO_STORE_CACHE_CONTROL = "private, no-store"
INLINE_DISPOSITION = "inline"
ATTACHMENT_DISPOSITION = "attachment"


@router.get("/files/{drive_file_id}/content")
async def get_drive_file_content_endpoint(
    project_id: UUID,
    drive_file_id: str,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
    gateway: DriveGatewayDep,
    download: bool = False,
) -> Response:
    try:
        preview = await load_drive_file_preview(
            session, gateway, project_id, drive_file_id, attachment=download
        )
    except DriveFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy file trong dự án này"
        ) from None
    except DrivePreviewNotAllowedError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Loại file này không xem trực tiếp được, hãy tải về",
        ) from None
    except DrivePreviewTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File vượt quá giới hạn xem trực tiếp",
        ) from None
    except DriveApiError as error:
        logger.error("Tải file Drive thất bại: project=%s status=%s", project_id, error.status)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=DRIVE_UNAVAILABLE_DETAIL
        ) from None

    disposition = ATTACHMENT_DISPOSITION if download else INLINE_DISPOSITION
    return Response(
        content=preview.content,
        media_type=preview.media_type,
        headers={
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(preview.file_name)}",
            "Cache-Control": NO_STORE_CACHE_CONTROL,
            "X-Content-Type-Options": "nosniff",
        },
    )
