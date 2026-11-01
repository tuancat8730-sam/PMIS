from collections.abc import Mapping
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.it_gate_rules import is_gated_milestone
from app.core.schedule_rules import effective_due_date, hard_deadline_respected
from app.models.milestone import Milestone, StoredMilestoneStatus
from app.models.milestone_adjustment import MilestoneAdjustment
from app.models.project import Project, ProjectArchetype
from app.services.hold_points import blocking_hold_point_codes
from app.services.it_gate import it_completion_blockers_for_project

HARD_DEADLINE_MESSAGE = "Mốc cứng không được lùi quá hạn gốc"
LOCKED_CHANGE_REASON_MESSAGE = "Thay đổi hạn của mốc đã khóa cần ghi lý do"
COMPLETION_BLOCKED_MESSAGE = "Chưa thể hoàn thành mốc, điểm dừng chưa đủ xác nhận 3 bên"
IT_GATE_BLOCKED_MESSAGE = "Chưa thể nghiệm thu dự án CNTT"


class DuplicateMilestoneError(Exception):
    """Mã mốc đã tồn tại trong dự án."""


class ScheduleRuleError(Exception):
    """Vi phạm quy tắc tiến độ; thông điệp viết tiếng Việt để trả cho người dùng."""


async def get_milestone(
    session: AsyncSession,
    project_id: UUID,
    milestone_id: UUID,
) -> Milestone | None:
    result = await session.execute(
        select(Milestone).where(
            Milestone.id == milestone_id,
            Milestone.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def find_milestone_by_code(
    session: AsyncSession,
    project_id: UUID,
    code: str,
) -> Milestone | None:
    result = await session.execute(
        select(Milestone).where(Milestone.project_id == project_id, Milestone.code == code)
    )
    return result.scalar_one_or_none()


async def list_milestones(session: AsyncSession, project_id: UUID) -> list[Milestone]:
    result = await session.execute(
        select(Milestone).where(Milestone.project_id == project_id).order_by(Milestone.code)
    )
    return list(result.scalars().all())


async def create_milestone(
    session: AsyncSession,
    *,
    project_id: UUID,
    values: Mapping[str, Any],
) -> Milestone:
    if not hard_deadline_respected(
        bool(values["is_hard_deadline"]),
        values["baseline_end"],
        values.get("adjusted_end"),
    ):
        raise ScheduleRuleError(HARD_DEADLINE_MESSAGE)

    milestone = Milestone(project_id=project_id, **values)
    session.add(milestone)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateMilestoneError(str(values["code"])) from exc
    return milestone


def _is_locked(milestone: Milestone) -> bool:
    """Mốc khóa là mốc đã hoàn thành hoặc mốc cứng. Đổi hạn mốc khóa phải có bản ghi điều chỉnh."""
    return milestone.status == StoredMilestoneStatus.COMPLETED or milestone.is_hard_deadline


async def _check_completion_allowed(session: AsyncSession, milestone: Milestone) -> None:
    blockers = await blocking_hold_point_codes(session, milestone.id)
    if blockers:
        raise ScheduleRuleError(f"{COMPLETION_BLOCKED_MESSAGE}: {', '.join(blockers)}")
    await _check_it_gate(session, milestone)


async def _check_it_gate(session: AsyncSession, milestone: Milestone) -> None:
    """Mốc M8 của dự án CNTT chỉ hoàn thành khi qua cổng ATTT, pentest và NFR (E8)."""
    if not is_gated_milestone(milestone.code):
        return
    project = await session.get(Project, milestone.project_id)
    if project is None or project.archetype != ProjectArchetype.IT_SYSTEM:
        return
    blockers = await it_completion_blockers_for_project(session, milestone.project_id)
    if blockers:
        raise ScheduleRuleError(f"{IT_GATE_BLOCKED_MESSAGE}: {'; '.join(blockers)}")


async def update_milestone(
    session: AsyncSession,
    milestone: Milestone,
    *,
    changes: Mapping[str, Any],
    reason: str | None,
    actor_id: UUID,
) -> MilestoneAdjustment | None:
    """Áp thay đổi lên mốc đã nạp trong session. Trả về bản ghi điều chỉnh khi đổi hạn mốc khóa."""
    if changes.get("status") == StoredMilestoneStatus.COMPLETED:
        await _check_completion_allowed(session, milestone)

    new_adjusted_end: date | None = changes.get("adjusted_end", milestone.adjusted_end)
    if not hard_deadline_respected(
        milestone.is_hard_deadline, milestone.baseline_end, new_adjusted_end
    ):
        raise ScheduleRuleError(HARD_DEADLINE_MESSAGE)

    date_changed = "adjusted_end" in changes and changes["adjusted_end"] != milestone.adjusted_end
    needs_record = date_changed and _is_locked(milestone)
    if needs_record and not reason:
        raise ScheduleRuleError(LOCKED_CHANGE_REASON_MESSAGE)

    previous_due = effective_due_date(milestone.baseline_end, milestone.adjusted_end)
    for field, value in changes.items():
        setattr(milestone, field, value)
    await session.flush()

    if not needs_record:
        return None

    adjustment = MilestoneAdjustment(
        milestone_id=milestone.id,
        reason=reason,
        previous_end=previous_due,
        new_end=effective_due_date(milestone.baseline_end, milestone.adjusted_end),
        created_by=actor_id,
    )
    session.add(adjustment)
    await session.flush()
    return adjustment
