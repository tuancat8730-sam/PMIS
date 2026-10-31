from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.penalty_rule import PenaltyRule


class DuplicatePenaltyRuleError(Exception):
    """Đã có ngưỡng phạt với ngày hiệu lực này trong dự án."""


async def list_penalty_rules(session: AsyncSession, project_id: UUID) -> list[PenaltyRule]:
    result = await session.execute(
        select(PenaltyRule)
        .where(PenaltyRule.project_id == project_id)
        .order_by(PenaltyRule.effective_from.desc())
    )
    return list(result.scalars().all())


async def create_penalty_rule(
    session: AsyncSession,
    *,
    project_id: UUID,
    values: dict[str, Any],
) -> PenaltyRule:
    rule = PenaltyRule(project_id=project_id, **values)
    session.add(rule)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicatePenaltyRuleError(str(values["effective_from"])) from exc
    return rule


async def effective_penalty_rule(
    session: AsyncSession,
    project_id: UUID,
    on: date,
) -> PenaltyRule | None:
    """Ngưỡng có hiệu lực vào ngày `on`: bản ghi có ngày hiệu lực gần nhất không vượt quá `on`."""
    result = await session.execute(
        select(PenaltyRule)
        .where(PenaltyRule.project_id == project_id, PenaltyRule.effective_from <= on)
        .order_by(PenaltyRule.effective_from.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
