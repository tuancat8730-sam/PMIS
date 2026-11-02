from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.schemas.file_register import FileRegisterCreate, FileRegisterOut, FileRegisterUpdate
from app.services.audit import record_audit
from app.services.file_register import (
    DuplicateSttError,
    ForeignDriveFileError,
    create_file_entry,
    ensure_drive_file_in_project,
    get_file_entry,
    list_file_entries,
    update_file_entry,
)

FILE_ENTRY_NOT_FOUND_DETAIL = "Không tìm thấy dòng file trong register"
DUPLICATE_STT_DETAIL = "Số thứ tự đã tồn tại trong register của dự án này"
FOREIGN_DRIVE_FILE_DETAIL = "File Drive không thuộc dự án này"

router = APIRouter(prefix="/projects/{project_id}/file-register", tags=["file-register"])


@router.get("", response_model=list[FileRegisterOut])
async def list_file_register_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[FileRegisterOut]:
    entries = await list_file_entries(session, project_id)
    return [FileRegisterOut.model_validate(entry) for entry in entries]


@router.post("", response_model=FileRegisterOut, status_code=status.HTTP_201_CREATED)
async def create_file_register_endpoint(
    project_id: UUID,
    payload: FileRegisterCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> FileRegisterOut:
    values = payload.model_dump()
    await _ensure_linked_file_in_project(session, project_id, values["drive_file_id"])
    try:
        entry = await create_file_entry(session, project_id=project_id, values=values)
    except DuplicateSttError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_STT_DETAIL
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="file_register.create",
        entity_type="file_register",
        entity_id=str(entry.id),
        changes={"stt": entry.stt},
    )
    output = FileRegisterOut.model_validate(entry)
    await session.commit()
    return output


@router.patch("/{entry_id}", response_model=FileRegisterOut)
async def update_file_register_endpoint(
    project_id: UUID,
    entry_id: UUID,
    payload: FileRegisterUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> FileRegisterOut:
    entry = await get_file_entry(session, project_id, entry_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=FILE_ENTRY_NOT_FOUND_DETAIL
        )
    changes = payload.model_dump(exclude_unset=True)
    if "drive_file_id" in changes:
        await _ensure_linked_file_in_project(session, project_id, changes["drive_file_id"])
    update_file_entry(entry, changes)
    await session.flush()

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="file_register.update",
        entity_type="file_register",
        entity_id=str(entry.id),
        changes={key: None if value is None else str(value) for key, value in changes.items()},
    )
    output = FileRegisterOut.model_validate(entry)
    await session.commit()
    return output


async def _ensure_linked_file_in_project(
    session: AsyncSession,
    project_id: UUID,
    drive_file_id: UUID | None,
) -> None:
    try:
        await ensure_drive_file_in_project(session, project_id, drive_file_id)
    except ForeignDriveFileError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=FOREIGN_DRIVE_FILE_DETAIL
        ) from None
