"""tao bang e10 hien truong: idempotency_keys va cot version

Revision ID: d2f6b8c4e1a9
Revises: c5d9a1e7f3b2
Create Date: 2026-11-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2f6b8c4e1a9"
down_revision: str | None = "c5d9a1e7f3b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VERSIONED_TABLES: tuple[str, ...] = ("delivery_handovers", "equipment_serials")


def _create_idempotency_keys() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column("endpoint", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_idempotency_keys")),
        sa.UniqueConstraint(
            "device_id",
            "idempotency_key",
            name="uq_idempotency_keys_device_key",
        ),
    )


def _add_version_columns() -> None:
    for table in VERSIONED_TABLES:
        op.add_column(
            table,
            sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        )


def upgrade() -> None:
    _create_idempotency_keys()
    _add_version_columns()


def downgrade() -> None:
    for table in reversed(VERSIONED_TABLES):
        op.drop_column(table, "version")
    op.drop_table("idempotency_keys")
