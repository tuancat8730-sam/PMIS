"""them cot removed_at vao drive_files (Pha 1 E5: danh dau file da xoa tren Drive)

Revision ID: d5e9b3a7f1c2
Revises: c4f8a2d6e1b9
Create Date: 2026-11-02 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5e9b3a7f1c2"
down_revision: str | None = "c4f8a2d6e1b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "drive_files",
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("drive_files", "removed_at")
