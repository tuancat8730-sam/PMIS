from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schedule_rules import missing_confirmation_parties
from app.models.hold_point import ConfirmingParty, HoldPoint, HoldPointConfirmation

REQUIRED_PARTIES: frozenset[str] = frozenset(party.value for party in ConfirmingParty)


class DuplicateHoldPointError(Exception):
    """Mã điểm dừng đã tồn tại trong dự án."""


class DuplicateConfirmationError(Exception):
    """Bên này đã xác nhận điểm dừng."""


async def get_hold_point(
    session: AsyncSession,
    project_id: UUID,
    hold_point_id: UUID,
) -> HoldPoint | None:
    result = await session.execute(
        select(HoldPoint).where(
            HoldPoint.id == hold_point_id,
            HoldPoint.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def list_hold_points(session: AsyncSession, project_id: UUID) -> list[HoldPoint]:
    result = await session.execute(
        select(HoldPoint).where(HoldPoint.project_id == project_id).order_by(HoldPoint.code)
    )
    return list(result.scalars().all())


async def confirmed_parties_by_hold_point(
    session: AsyncSession,
    hold_point_ids: Iterable[UUID],
) -> dict[UUID, set[str]]:
    ids = list(hold_point_ids)
    confirmed: dict[UUID, set[str]] = {hold_point_id: set() for hold_point_id in ids}
    if not ids:
        return confirmed
    result = await session.execute(
        select(HoldPointConfirmation.hold_point_id, HoldPointConfirmation.party).where(
            HoldPointConfirmation.hold_point_id.in_(ids)
        )
    )
    for hold_point_id, party in result.all():
        confirmed[hold_point_id].add(party.value)
    return confirmed


async def blocking_hold_point_codes(session: AsyncSession, milestone_id: UUID) -> list[str]:
    """Mã các điểm dừng gắn với mốc mà chưa đủ xác nhận của cả 3 bên."""
    result = await session.execute(
        select(HoldPoint).where(HoldPoint.milestone_id == milestone_id).order_by(HoldPoint.code)
    )
    hold_points = list(result.scalars().all())
    confirmed = await confirmed_parties_by_hold_point(session, [hp.id for hp in hold_points])
    return [
        hold_point.code
        for hold_point in hold_points
        if missing_confirmation_parties(confirmed[hold_point.id], REQUIRED_PARTIES)
    ]


async def create_hold_point(
    session: AsyncSession,
    *,
    project_id: UUID,
    code: str,
    name: str,
    milestone_id: UUID | None,
) -> HoldPoint:
    hold_point = HoldPoint(project_id=project_id, code=code, name=name, milestone_id=milestone_id)
    session.add(hold_point)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateHoldPointError(code) from exc
    return hold_point


async def add_confirmation(
    session: AsyncSession,
    *,
    hold_point: HoldPoint,
    party: ConfirmingParty,
    evidence_ref: str,
    confirmed_by: UUID,
) -> HoldPointConfirmation:
    confirmation = HoldPointConfirmation(
        hold_point_id=hold_point.id,
        party=party,
        evidence_ref=evidence_ref,
        confirmed_by=confirmed_by,
    )
    session.add(confirmation)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateConfirmationError(party.value) from exc
    return confirmation
