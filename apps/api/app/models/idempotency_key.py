import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IdempotencyKey(Base):
    """Kết quả đầu tiên của một lệnh ghi từ thiết bị, dùng để trả lại khi thiết bị gửi lại."""

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint(
            "device_id",
            "idempotency_key",
            name="uq_idempotency_keys_device_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    device_id: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[uuid.UUID] = mapped_column()
    endpoint: Mapped[str] = mapped_column(String(200))
    request_hash: Mapped[str] = mapped_column(String(64))
    status_code: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
