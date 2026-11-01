import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.integrations.drive import DriveApiError, GoogleDriveGateway
from app.integrations.drive_gateway import DriveGateway
from app.models.project import Project
from app.schemas.drive import DriveFileOut, DriveMatchSuggestionOut, DriveSyncOut
from app.services.audit import record_audit
from app.services.drive_sync import (
    DriveRootNotConfiguredError,
    list_project_drive_files,
    suggest_drive_matches,
    sync_project_drive,
)

logger = logging.getLogger(__name__)

DRIVE_NOT_CONFIGURED_DETAIL = "Máy chủ chưa cấu hình tài khoản dịch vụ Google Drive"
DRIVE_ROOT_NOT_CONFIGURED_DETAIL = "Dự án chưa khai báo thư mục gốc trên Google Drive"
DRIVE_UNAVAILABLE_DETAIL = "Google Drive đang từ chối yêu cầu, hãy thử lại sau"

router = APIRouter(prefix="/projects/{project_id}/drive", tags=["drive"])


def get_drive_gateway(request: Request) -> DriveGateway:
    key_file_path = request.app.state.settings.drive_service_account_file
    if key_file_path is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=DRIVE_NOT_CONFIGURED_DETAIL
        )
    return GoogleDriveGateway.from_service_account_file(key_file_path)


DriveGatewayDep = Annotated[DriveGateway, Depends(get_drive_gateway)]


@router.post("/sync", response_model=DriveSyncOut)
async def sync_drive_endpoint(
    project_id: UUID,
    project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    gateway: DriveGatewayDep,
    _rate_limit: WriteRateLimitDep,
) -> DriveSyncOut:
    try:
        result = await sync_project_drive(session, gateway, project)
    except DriveRootNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DRIVE_ROOT_NOT_CONFIGURED_DETAIL
        ) from None
    except DriveApiError as error:
        await session.rollback()
        logger.error("Đồng bộ Drive thất bại: project=%s status=%s", project_id, error.status)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=DRIVE_UNAVAILABLE_DETAIL
        ) from None

    output = DriveSyncOut(scanned=result.scanned, created=result.created, updated=result.updated)
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="drive.sync",
        entity_type="project",
        entity_id=str(project_id),
        changes=output.model_dump(),
    )
    await session.commit()
    return output


@router.get("/suggestions", response_model=list[DriveMatchSuggestionOut])
async def list_drive_suggestions_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[DriveMatchSuggestionOut]:
    suggestions = await suggest_drive_matches(session, project_id)
    return [
        DriveMatchSuggestionOut(
            drive_file_id=suggestion.drive_file_id,
            document_id=suggestion.document_id,
            reason=suggestion.reason,
        )
        for suggestion in suggestions
    ]


@router.get("/files", response_model=list[DriveFileOut])
async def list_drive_files_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[DriveFileOut]:
    rows = await list_project_drive_files(session, project_id)
    return [DriveFileOut.model_validate(row) for row in rows]
