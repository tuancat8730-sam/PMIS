from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.legal_document import DocMaturityStatus, LegalDocument, LegalPhaseGroup
from app.models.project import Project
from app.schemas.legal_documents import (
    LegalDocumentCreate,
    LegalDocumentOut,
    LegalDocumentSummary,
    LegalDocumentTransition,
    LegalDocumentUpdate,
)
from app.services.audit import record_audit
from app.services.legal_documents import (
    DuplicateSttError,
    LockedDocumentError,
    ReasonRequiredError,
    StatusConflictError,
    build_summary,
    count_by_phase_and_status,
    create_legal_document,
    get_legal_document,
    list_legal_documents,
    transition_legal_document,
    update_legal_document,
)

LEGAL_DOCUMENT_NOT_FOUND_DETAIL = "Không tìm thấy hồ sơ pháp lý"
DUPLICATE_STT_DETAIL = "Số thứ tự đã tồn tại trong checklist của dự án này"
LOCKED_DOCUMENT_DETAIL = "Hồ sơ đã đóng, không sửa trực tiếp được. Hãy mở lại hồ sơ trước"
REASON_REQUIRED_DETAIL = "Chuyển trạng thái này cần ghi lý do"

router = APIRouter(prefix="/projects/{project_id}/legal-documents", tags=["legal-documents"])


@router.post("", response_model=LegalDocumentOut, status_code=status.HTTP_201_CREATED)
async def create_legal_document_endpoint(
    project_id: UUID,
    payload: LegalDocumentCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> LegalDocumentOut:
    try:
        document = await create_legal_document(
            session,
            project_id=project_id,
            values=payload.model_dump(),
        )
    except DuplicateSttError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_STT_DETAIL
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="legal_document.create",
        entity_type="legal_document",
        entity_id=str(document.id),
        changes={"stt": document.stt},
    )
    output = LegalDocumentOut.model_validate(document)
    await session.commit()
    return output


@router.get("", response_model=list[LegalDocumentOut])
async def list_legal_documents_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
    phase_group: Annotated[LegalPhaseGroup | None, Query()] = None,
    maturity_status: Annotated[DocMaturityStatus | None, Query()] = None,
) -> list[LegalDocumentOut]:
    documents = await list_legal_documents(session, project_id, phase_group, maturity_status)
    return [LegalDocumentOut.model_validate(document) for document in documents]


# Khai báo trước route có tham số `{document_id}` để "summary" không bị hiểu là UUID.
@router.get("/summary", response_model=LegalDocumentSummary)
async def legal_documents_summary_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> LegalDocumentSummary:
    rows = await count_by_phase_and_status(session, project_id)
    return build_summary(rows)


async def _get_document_or_404(
    session: SessionDep,
    project_id: UUID,
    document_id: UUID,
) -> LegalDocument:
    document = await get_legal_document(session, project_id, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=LEGAL_DOCUMENT_NOT_FOUND_DETAIL
        )
    return document


@router.get("/{document_id}", response_model=LegalDocumentOut)
async def get_legal_document_endpoint(
    project_id: UUID,
    document_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> LegalDocumentOut:
    document = await _get_document_or_404(session, project_id, document_id)
    return LegalDocumentOut.model_validate(document)


@router.patch("/{document_id}", response_model=LegalDocumentOut)
async def update_legal_document_endpoint(
    project_id: UUID,
    document_id: UUID,
    payload: LegalDocumentUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> LegalDocumentOut:
    document = await _get_document_or_404(session, project_id, document_id)
    changes = payload.model_dump(exclude_unset=True)
    try:
        update_legal_document(document, changes)
    except LockedDocumentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=LOCKED_DOCUMENT_DETAIL
        ) from None
    await session.flush()

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="legal_document.update",
        entity_type="legal_document",
        entity_id=str(document.id),
        changes=_audit_changes(changes),
    )
    output = LegalDocumentOut.model_validate(document)
    await session.commit()
    return output


@router.post("/{document_id}/transitions", response_model=LegalDocumentOut)
async def transition_legal_document_endpoint(
    project_id: UUID,
    document_id: UUID,
    payload: LegalDocumentTransition,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> LegalDocumentOut:
    document = await _get_document_or_404(session, project_id, document_id)
    try:
        previous = transition_legal_document(
            document,
            expected_status=payload.expected_status,
            target_status=payload.target_status,
            reason=payload.reason,
        )
    except StatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except ReasonRequiredError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=REASON_REQUIRED_DETAIL
        ) from None

    changes: dict[str, Any] = {"from": previous.value, "to": payload.target_status.value}
    if payload.reason and payload.reason.strip():
        changes["reason"] = payload.reason.strip()
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="legal_document.transition",
        entity_type="legal_document",
        entity_id=str(document.id),
        changes=changes,
    )
    output = LegalDocumentOut.model_validate(document)
    await session.commit()
    return output


def _audit_changes(changes: dict[str, Any]) -> dict[str, str | None]:
    return {key: None if value is None else str(value) for key, value in changes.items()}
