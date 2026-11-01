"""Dịch vụ module CNTT: phân hệ, khảo sát, RTM, pentest, số đo NFR. Service không commit."""

from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models.it_survey_record import ItSurveyRecord
from app.models.it_system_module import ItSystemModule
from app.models.nfr_measurement import NfrMeasurement
from app.models.pentest_finding import PentestFinding
from app.models.rtm_link import RtmLink


class DuplicateItRecordError(Exception):
    """Khóa nghiệp vụ đã tồn tại trong dự án (mã phân hệ, tên đơn vị)."""


async def _get_scoped[ModelT: Base](
    session: AsyncSession,
    model: type[ModelT],
    project_id: UUID,
    record_id: UUID,
) -> ModelT | None:
    result = await session.execute(
        select(model).where(model.id == record_id, model.project_id == project_id)  # type: ignore[attr-defined]  # noqa: E501
    )
    return result.scalar_one_or_none()


async def _list_scoped[ModelT: Base](
    session: AsyncSession,
    model: type[ModelT],
    project_id: UUID,
) -> list[ModelT]:
    result = await session.execute(
        select(model).where(model.project_id == project_id)  # type: ignore[attr-defined]
    )
    return list(result.scalars().all())


async def _add[ModelT: Base](session: AsyncSession, record: ModelT, duplicate_key: str) -> ModelT:
    session.add(record)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateItRecordError(duplicate_key) from exc
    return record


def apply_changes[ModelT: Base](record: ModelT, changes: Mapping[str, Any]) -> ModelT:
    """Gán các trường đã đổi lên bản ghi đã nạp trong session."""
    for field, value in changes.items():
        setattr(record, field, value)
    return record


async def get_module(
    session: AsyncSession, project_id: UUID, module_id: UUID
) -> ItSystemModule | None:
    return await _get_scoped(session, ItSystemModule, project_id, module_id)


async def list_modules(session: AsyncSession, project_id: UUID) -> list[ItSystemModule]:
    return await _list_scoped(session, ItSystemModule, project_id)


async def create_module(
    session: AsyncSession, *, project_id: UUID, values: Mapping[str, Any]
) -> ItSystemModule:
    module = ItSystemModule(project_id=project_id, **values)
    return await _add(session, module, str(values["module_code"]))


async def get_survey_record(
    session: AsyncSession, project_id: UUID, record_id: UUID
) -> ItSurveyRecord | None:
    return await _get_scoped(session, ItSurveyRecord, project_id, record_id)


async def list_survey_records(session: AsyncSession, project_id: UUID) -> list[ItSurveyRecord]:
    return await _list_scoped(session, ItSurveyRecord, project_id)


async def create_survey_record(
    session: AsyncSession, *, project_id: UUID, values: Mapping[str, Any]
) -> ItSurveyRecord:
    record = ItSurveyRecord(project_id=project_id, **values)
    return await _add(session, record, str(values["unit_name"]))


async def list_rtm_links(session: AsyncSession, project_id: UUID) -> list[RtmLink]:
    return await _list_scoped(session, RtmLink, project_id)


async def create_rtm_link(
    session: AsyncSession, *, project_id: UUID, values: Mapping[str, Any]
) -> RtmLink:
    link = RtmLink(project_id=project_id, **values)
    session.add(link)
    await session.flush()
    return link


async def get_pentest_finding(
    session: AsyncSession, project_id: UUID, finding_id: UUID
) -> PentestFinding | None:
    return await _get_scoped(session, PentestFinding, project_id, finding_id)


async def list_pentest_findings(session: AsyncSession, project_id: UUID) -> list[PentestFinding]:
    return await _list_scoped(session, PentestFinding, project_id)


async def create_pentest_finding(
    session: AsyncSession, *, project_id: UUID, values: Mapping[str, Any]
) -> PentestFinding:
    finding = PentestFinding(project_id=project_id, **values)
    session.add(finding)
    await session.flush()
    return finding


async def record_nfr_measurement(
    session: AsyncSession,
    *,
    project_id: UUID,
    metric_key: str,
    measured: Decimal,
    recorded_by: UUID,
) -> NfrMeasurement:
    measurement = NfrMeasurement(
        project_id=project_id,
        metric_key=metric_key,
        measured=measured,
        recorded_by=recorded_by,
    )
    session.add(measurement)
    await session.flush()
    return measurement


async def latest_nfr_measurements(session: AsyncSession, project_id: UUID) -> dict[str, Decimal]:
    """Số đo mới nhất theo từng khóa chỉ tiêu."""
    result = await session.execute(
        select(NfrMeasurement)
        .where(NfrMeasurement.project_id == project_id)
        .order_by(NfrMeasurement.measured_at.desc(), NfrMeasurement.id.desc())
    )
    latest: dict[str, Decimal] = {}
    for measurement in result.scalars().all():
        latest.setdefault(measurement.metric_key, measurement.measured)
    return latest
