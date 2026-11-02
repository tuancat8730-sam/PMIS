import asyncio
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    FieldWriteHeadersDep,
    SessionDep,
    SettingsDep,
    WriteRateLimitDep,
    project_role_guard,
)
from app.core.delivery_matrix import DeliveryTransitionError
from app.core.field_rules import MAX_PHOTO_BYTES, hash_request_body, is_within_photo_size
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.schemas.field import (
    FieldGpsOut,
    FieldHandoverStatusOut,
    FieldHandoverStatusUpdate,
    FieldPhotoOut,
    FieldSerialVerificationOut,
    FieldSerialVerificationUpdate,
    PhotoKind,
)
from app.services.audit import record_audit
from app.services.delivery_handovers import update_handover_status
from app.services.field_photos import (
    PHOTO_REJECTED_DETAIL,
    PhotoInspection,
    PhotoRejectedError,
    build_photo_record,
    choose_gps,
    inspect_photo,
    store_photo_file,
)
from app.services.field_sync import (
    FieldWriteRequest,
    IdempotencyKeyReusedError,
    VersionConflictError,
    ensure_expected_version,
    find_recorded_response,
    lock_handover,
    lock_serial,
    record_response,
)

FIELD_WRITE_ROLES = (Role.PM, Role.SUPERVISION_CONSULTANT, Role.FIELD_ENGINEER)
HANDOVER_NOT_FOUND_DETAIL = "Không tìm thấy dòng giao hàng"
SERIAL_NOT_FOUND_DETAIL = "Không tìm thấy serial trong dự án"
PHOTO_TOO_LARGE_DETAIL = "Ảnh vượt quá dung lượng cho phép"
VERSION_CONFLICT_DETAIL = "Dữ liệu đã được thiết bị khác cập nhật. Tải lại trước khi thao tác"
IDEMPOTENCY_KEY_REUSED_DETAIL = "Idempotency-Key đã dùng cho một yêu cầu khác"
HTTP_OK = status.HTTP_200_OK
HTTP_CREATED = status.HTTP_201_CREATED
HTTP_CONFLICT = status.HTTP_409_CONFLICT

router = APIRouter(prefix="/projects/{project_id}/field", tags=["field"])


async def _replay_or_none(session: AsyncSession, request: FieldWriteRequest) -> JSONResponse | None:
    """Trả lại kết quả cũ nếu thiết bị gửi lại cùng khóa và cùng nội dung."""
    try:
        row = await find_recorded_response(session, request)
    except IdempotencyKeyReusedError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=IDEMPOTENCY_KEY_REUSED_DETAIL,
        ) from None
    if row is None:
        return None
    return JSONResponse(status_code=row.status_code, content=row.response_body)


def _conflict_response(exc: VersionConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_CONFLICT,
        content={"detail": VERSION_CONFLICT_DETAIL, "current": exc.current},
    )


@router.patch(
    "/delivery-handovers/{handover_id}/status",
    response_model=FieldHandoverStatusOut,
)
async def update_handover_status_endpoint(
    project_id: UUID,
    handover_id: UUID,
    payload: FieldHandoverStatusUpdate,
    _project: Annotated[Project, Depends(project_role_guard(*FIELD_WRITE_ROLES))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    headers: FieldWriteHeadersDep,
    _rate_limit: WriteRateLimitDep,
) -> Response:
    request = FieldWriteRequest(
        headers=headers,
        endpoint=f"PATCH field/delivery-handovers/{handover_id}/status",
        request_hash=hash_request_body(payload.model_dump_json().encode()),
    )
    replay = await _replay_or_none(session, request)
    if replay is not None:
        return replay

    handover = await lock_handover(session, project_id=project_id, handover_id=handover_id)
    if handover is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HANDOVER_NOT_FOUND_DETAIL)
    previous_status = handover.delivery_status
    current = {"delivery_status": previous_status, "version": handover.version}
    try:
        ensure_expected_version(handover.version, payload.expected_version, current)
        update_handover_status(handover, payload.delivery_status)
    except VersionConflictError as exc:
        await session.rollback()
        return _conflict_response(exc)
    except DeliveryTransitionError as exc:
        await session.rollback()
        raise HTTPException(status_code=HTTP_CONFLICT, detail=str(exc)) from None

    handover.version += 1
    output = FieldHandoverStatusOut(
        id=handover.id,
        delivery_status=handover.delivery_status,
        version=handover.version,
    )
    body = output.model_dump(mode="json")
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="field.delivery_status",
        entity_type="delivery_handover",
        entity_id=str(handover.id),
        changes={
            "from": previous_status,
            "to": handover.delivery_status,
            "device_id": headers.device_id,
        },
    )
    record_response(session, request, status_code=HTTP_OK, body=body)
    await session.commit()
    return output


@router.patch(
    "/serials/{serial_id}/verification",
    response_model=FieldSerialVerificationOut,
)
async def update_serial_verification_endpoint(
    project_id: UUID,
    serial_id: UUID,
    payload: FieldSerialVerificationUpdate,
    _project: Annotated[Project, Depends(project_role_guard(*FIELD_WRITE_ROLES))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    headers: FieldWriteHeadersDep,
    _rate_limit: WriteRateLimitDep,
) -> Response:
    request = FieldWriteRequest(
        headers=headers,
        endpoint=f"PATCH field/serials/{serial_id}/verification",
        request_hash=hash_request_body(payload.model_dump_json().encode()),
    )
    replay = await _replay_or_none(session, request)
    if replay is not None:
        return replay

    serial = await lock_serial(session, project_id=project_id, serial_id=serial_id)
    if serial is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SERIAL_NOT_FOUND_DETAIL)
    current = {"verification_status": serial.verification_status, "version": serial.version}
    try:
        ensure_expected_version(serial.version, payload.expected_version, current)
    except VersionConflictError as exc:
        await session.rollback()
        return _conflict_response(exc)

    previous_status = serial.verification_status
    serial.verification_status = payload.verification_status
    serial.version += 1
    output = FieldSerialVerificationOut(
        id=serial.id,
        verification_status=serial.verification_status,
        version=serial.version,
    )
    body = output.model_dump(mode="json")
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="field.serial_verification",
        entity_type="equipment_serial",
        entity_id=str(serial.id),
        changes={
            "from": previous_status,
            "to": serial.verification_status,
            "device_id": headers.device_id,
        },
    )
    record_response(session, request, status_code=HTTP_OK, body=body)
    await session.commit()
    return output


async def _inspect_or_reject(content: bytes) -> PhotoInspection:
    # Pillow đồng bộ và có thể tốn CPU, nên chạy trong thread riêng để không chặn event loop.
    try:
        return await asyncio.to_thread(inspect_photo, content)
    except PhotoRejectedError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=PHOTO_REJECTED_DETAIL,
        ) from None


@router.post(
    "/delivery-handovers/{handover_id}/photos",
    response_model=FieldPhotoOut,
    status_code=HTTP_CREATED,
)
async def upload_handover_photo_endpoint(
    project_id: UUID,
    handover_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*FIELD_WRITE_ROLES))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    headers: FieldWriteHeadersDep,
    settings: SettingsDep,
    _rate_limit: WriteRateLimitDep,
    file: Annotated[UploadFile, File()],
    kind: Annotated[PhotoKind, Form()],
    latitude: Annotated[float | None, Form(ge=-90, le=90)] = None,
    longitude: Annotated[float | None, Form(ge=-180, le=180)] = None,
) -> Response:
    # Đọc có giới hạn để tệp quá lớn không làm đầy bộ nhớ.
    content = await file.read(MAX_PHOTO_BYTES + 1)
    if not is_within_photo_size(len(content)):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=PHOTO_TOO_LARGE_DETAIL,
        )
    content_digest = hashlib.sha256(content).hexdigest()
    request = FieldWriteRequest(
        headers=headers,
        endpoint=f"POST field/delivery-handovers/{handover_id}/photos",
        request_hash=hash_request_body(
            f"{content_digest}|{kind}|{latitude}|{longitude}".encode(),
        ),
    )
    replay = await _replay_or_none(session, request)
    if replay is not None:
        return replay

    inspection = await _inspect_or_reject(content)
    handover = await lock_handover(session, project_id=project_id, handover_id=handover_id)
    if handover is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HANDOVER_NOT_FOUND_DETAIL)

    photo_id = uuid4()
    uploaded_at = datetime.now(UTC)
    storage_key = await store_photo_file(
        Path(settings.field_photo_dir),
        project_id=project_id,
        content=content,
        mime=inspection.mime,
        uploaded_at=uploaded_at,
    )
    gps = choose_gps(inspection.gps, latitude, longitude)
    record = build_photo_record(
        photo_id=photo_id,
        kind=kind,
        content=content,
        mime=inspection.mime,
        storage_key=storage_key,
        gps=gps,
        device_id=headers.device_id,
        uploaded_at=uploaded_at,
    )
    handover.site_photos = [*handover.site_photos, record]
    output = FieldPhotoOut(
        id=photo_id,
        kind=kind,
        mime=inspection.mime,
        size_bytes=len(content),
        gps=None if gps is None else FieldGpsOut.model_validate(gps, from_attributes=True),
        uploaded_at=uploaded_at,
    )
    body = output.model_dump(mode="json")
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="field.photo_upload",
        entity_type="delivery_handover",
        entity_id=str(handover.id),
        changes={"photo_id": str(photo_id), "kind": kind, "device_id": headers.device_id},
    )
    record_response(session, request, status_code=HTTP_CREATED, body=body)
    await session.commit()
    return output
