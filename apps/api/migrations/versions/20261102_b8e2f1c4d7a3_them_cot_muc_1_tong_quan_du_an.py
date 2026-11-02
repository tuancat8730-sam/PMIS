"""them cot muc I tong quan vao projects (dai dien phap luat, hinh thuc QLDA, han giai ngan)

Revision ID: b8e2f1c4d7a3
Revises: a7d3e9f2c1b8
Create Date: 2026-11-02 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8e2f1c4d7a3"
down_revision: str | None = "a7d3e9f2c1b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("legal_representative", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("qlda_form", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("disbursement_deadline", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "disbursement_deadline")
    op.drop_column("projects", "qlda_form")
    op.drop_column("projects", "legal_representative")
