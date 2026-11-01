from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.core.rtm_rules import RtmRow, orphan_rows
from app.models.project import Project
from app.schemas.it_system import (
    ModuleCreate,
    ModuleOut,
    ModuleUpdate,
    RtmCreate,
    RtmOrphanOut,
    RtmOut,
    SurveyCreate,
    SurveyOut,
    SurveyUpdate,
)
from app.services.audit import record_audit
from app.services.it_system import (
    DuplicateItRecordError,
    apply_changes,
    create_module,
    create_rtm_link,
    create_survey_record,
    get_module,
    get_survey_record,
    list_modules,
    list_rtm_links,
    list_survey_records,
)

MODULE_NOT_FOUND_DETAIL = "Không tìm thấy phân hệ"
SURVEY_NOT_FOUND_DETAIL = "Không tìm thấy đơn vị khảo sát"

router = APIRouter(prefix="/projects/{project_id}/it-system", tags=["it-system"])


@router.get("/modules", response_model=list[ModuleOut])
async def list_modules_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[ModuleOut]:
    modules = await list_modules(session, project_id)
    return [ModuleOut.model_validate(module) for module in modules]


@router.post("/modules", response_model=ModuleOut, status_code=status.HTTP_201_CREATED)
async def create_module_endpoint(
    project_id: UUID,
    payload: ModuleCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> ModuleOut:
    try:
        module = await create_module(session, project_id=project_id, values=payload.model_dump())
    except DuplicateItRecordError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mã phân hệ {exc} đã tồn tại trong dự án",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_module.create",
        entity_type="it_system_module",
        entity_id=str(module.id),
        changes={"module_code": module.module_code},
    )
    output = ModuleOut.model_validate(module)
    await session.commit()
    return output


@router.patch("/modules/{module_id}", response_model=ModuleOut)
async def update_module_endpoint(
    project_id: UUID,
    module_id: UUID,
    payload: ModuleUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> ModuleOut:
    module = await get_module(session, project_id, module_id)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MODULE_NOT_FOUND_DETAIL)
    changes = payload.model_dump(exclude_unset=True)
    apply_changes(module, changes)
    await session.flush()

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_module.update",
        entity_type="it_system_module",
        entity_id=str(module.id),
        changes={key: str(value) for key, value in changes.items()},
    )
    output = ModuleOut.model_validate(module)
    await session.commit()
    return output


@router.get("/survey-records", response_model=list[SurveyOut])
async def list_survey_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[SurveyOut]:
    records = await list_survey_records(session, project_id)
    return [SurveyOut.model_validate(record) for record in records]


@router.post("/survey-records", response_model=SurveyOut, status_code=status.HTTP_201_CREATED)
async def create_survey_endpoint(
    project_id: UUID,
    payload: SurveyCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> SurveyOut:
    try:
        record = await create_survey_record(
            session, project_id=project_id, values=payload.model_dump()
        )
    except DuplicateItRecordError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Đơn vị {exc} đã có bản ghi khảo sát trong dự án",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_survey.create",
        entity_type="it_survey_record",
        entity_id=str(record.id),
        changes={"unit_name": record.unit_name},
    )
    output = SurveyOut.model_validate(record)
    await session.commit()
    return output


@router.patch("/survey-records/{record_id}", response_model=SurveyOut)
async def update_survey_endpoint(
    project_id: UUID,
    record_id: UUID,
    payload: SurveyUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> SurveyOut:
    record = await get_survey_record(session, project_id, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SURVEY_NOT_FOUND_DETAIL)
    changes = payload.model_dump(exclude_unset=True)
    apply_changes(record, changes)
    await session.flush()

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_survey.update",
        entity_type="it_survey_record",
        entity_id=str(record.id),
        changes={key: str(value) for key, value in changes.items()},
    )
    output = SurveyOut.model_validate(record)
    await session.commit()
    return output


@router.get("/rtm-links", response_model=list[RtmOut])
async def list_rtm_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[RtmOut]:
    links = await list_rtm_links(session, project_id)
    return [RtmOut.model_validate(link) for link in links]


@router.post("/rtm-links", response_model=RtmOut, status_code=status.HTTP_201_CREATED)
async def create_rtm_endpoint(
    project_id: UUID,
    payload: RtmCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> RtmOut:
    link = await create_rtm_link(session, project_id=project_id, values=payload.model_dump())
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_rtm.create",
        entity_type="rtm_link",
        entity_id=str(link.id),
    )
    output = RtmOut.model_validate(link)
    await session.commit()
    return output


@router.get("/rtm-links/orphans", response_model=list[RtmOrphanOut])
async def rtm_orphans_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[RtmOrphanOut]:
    links = await list_rtm_links(session, project_id)
    rows = tuple(
        RtmRow(
            appendix_c_ref=link.appendix_c_ref,
            srs_ref=link.srs_ref,
            module_code=link.module_code,
            test_case_ref=link.test_case_ref,
        )
        for link in links
    )
    return [
        RtmOrphanOut(row_index=index, missing_links=sorted(missing))
        for index, missing in orphan_rows(rows)
    ]
