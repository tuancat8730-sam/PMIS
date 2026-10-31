from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def record_audit(
    session: AsyncSession,
    *,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    changes: dict[str, Any] | None = None,
) -> None:
    """Thêm dòng nhật ký vào session. Caller chịu trách nhiệm commit cùng thao tác nghiệp vụ."""
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes or {},
        ),
    )
