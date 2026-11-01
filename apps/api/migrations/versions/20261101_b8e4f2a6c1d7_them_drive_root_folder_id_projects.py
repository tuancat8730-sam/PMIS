"""them cot drive_root_folder_id cho projects (E5 Google Drive)

Revision ID: b8e4f2a6c1d7
Revises: a7d3e9b1c5f2
Create Date: 2026-11-01 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8e4f2a6c1d7"
down_revision: str | None = "a7d3e9b1c5f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("drive_root_folder_id", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "drive_root_folder_id")
