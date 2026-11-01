"""Nạp module CNTT của SGD-HCM: phân hệ A–G, ngưỡng NFR (spec Phân hệ 5), đơn vị khảo sát (spec §7).

Chạy sau `seed_real_projects`. Chạy lại an toàn: bản ghi đã có được bỏ qua.
Tên phân hệ tạm là "Phân hệ X" đến khi có tên chuẩn (Q7); sửa qua PATCH module.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.seed_real_projects import (
    HCM_PROJECT,
    HCM_UNITS_FILE,
    find_project_by_code,
    load_seed_rows,
)
from app.schemas.it_system import ModuleCreate
from app.services.audit import record_audit
from app.services.it_system import (
    create_module,
    create_survey_record,
    list_modules,
    list_survey_records,
)

logger = logging.getLogger(__name__)

IT_MODULE_CODES: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G")
# Ngưỡng nghiệm thu theo spec Phân hệ 5, mục 2. Lưu trong nfr_metrics của từng phân hệ.
HCM_NFR_CRITERIA: dict[str, dict[str, Any]] = {
    "ccu": {"comparison": "AT_LEAST", "threshold": "3600"},
    "accounts": {"comparison": "AT_LEAST", "threshold": "5170"},
    "avg_response_s": {"comparison": "BELOW", "threshold": "2"},
    "page_load_4g_s": {"comparison": "BELOW", "threshold": "3"},
    "report_s": {"comparison": "AT_MOST", "threshold": "10"},
    "uptime_percent": {"comparison": "AT_LEAST", "threshold": "99.9"},
    "rto_hours": {"comparison": "AT_MOST", "threshold": "4"},
    "backup_retention_days": {"comparison": "AT_LEAST", "threshold": "30"},
    "audit_retention_months": {"comparison": "AT_LEAST", "threshold": "12"},
}


async def ensure_modules(session: AsyncSession, project_id: UUID) -> int:
    existing = {module.module_code for module in await list_modules(session, project_id)}
    inserted = 0
    for code in IT_MODULE_CODES:
        if code in existing:
            continue
        payload = ModuleCreate(
            module_code=code,
            module_name=f"Phân hệ {code}",
            dev_progress=Decimal("0"),
            nfr_metrics=HCM_NFR_CRITERIA,
        )
        module = await create_module(session, project_id=project_id, values=payload.model_dump())
        await record_audit(
            session,
            actor_id=None,
            action="it_module.seed",
            entity_type="it_system_module",
            entity_id=str(module.id),
            changes={"module_code": code},
        )
        inserted += 1
    return inserted


async def ensure_survey_units(
    session: AsyncSession,
    project_id: UUID,
    rows: list[dict[str, Any]],
) -> int:
    existing = {record.unit_name for record in await list_survey_records(session, project_id)}
    inserted = 0
    for row in rows:
        unit_name = str(row["official_name"])
        if unit_name in existing:
            continue
        record = await create_survey_record(
            session, project_id=project_id, values={"unit_name": unit_name}
        )
        await record_audit(
            session,
            actor_id=None,
            action="it_survey.seed",
            entity_type="it_survey_record",
            entity_id=str(record.id),
            changes={"unit_name": unit_name},
        )
        inserted += 1
    return inserted


async def seed_it_system(session_factory: async_sessionmaker[AsyncSession]) -> tuple[int, int]:
    """Nạp phân hệ và đơn vị khảo sát trong một transaction; trả về (số phân hệ, số đơn vị) mới."""
    async with session_factory() as session:
        project = await find_project_by_code(session, HCM_PROJECT.code)
        if project is None:
            raise ValueError(f"Chưa có dự án {HCM_PROJECT.code}; chạy seed_real_projects trước")
        modules = await ensure_modules(session, project.id)
        units = await ensure_survey_units(session, project.id, load_seed_rows(HCM_UNITS_FILE))
        await session.commit()
    logger.info("Seed %s: thêm %d phân hệ, %d đơn vị khảo sát", HCM_PROJECT.code, modules, units)
    return modules, units


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)

    async def _run() -> None:
        try:
            await seed_it_system(async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
