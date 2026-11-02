from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.milestone_note import MilestoneNote


async def list_notes_by_milestone(
    session: AsyncSession,
    milestone_ids: Sequence[UUID],
) -> dict[UUID, list[MilestoneNote]]:
    """Gom ghi chú theo mốc, mới nhất trước, bằng một truy vấn."""
    grouped: dict[UUID, list[MilestoneNote]] = {milestone_id: [] for milestone_id in milestone_ids}
    if not milestone_ids:
        return grouped
    result = await session.execute(
        select(MilestoneNote)
        .where(MilestoneNote.milestone_id.in_(milestone_ids))
        .order_by(MilestoneNote.created_at.desc())
    )
    for note in result.scalars().all():
        grouped[note.milestone_id].append(note)
    return grouped


async def add_note(
    session: AsyncSession,
    *,
    milestone_id: UUID,
    body: str,
    author_id: UUID,
) -> MilestoneNote:
    """Chỉ thêm ghi chú. Không có hàm sửa hay xóa để giữ nhật ký nguyên vẹn."""
    note = MilestoneNote(milestone_id=milestone_id, body=body, created_by=author_id)
    session.add(note)
    await session.flush()
    return note
