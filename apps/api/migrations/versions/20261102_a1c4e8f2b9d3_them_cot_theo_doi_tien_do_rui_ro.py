"""them cot theo doi tien do va rui ro (Pha 1 tracking)

Revision ID: a1c4e8f2b9d3
Revises: d2f6b8c4e1a9
Create Date: 2026-11-02 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1c4e8f2b9d3"
down_revision: str | None = "d2f6b8c4e1a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RISK_LEVEL_VALUES = ("LOW", "MEDIUM", "HIGH", "VERY_HIGH")


def upgrade() -> None:
    op.add_column("milestones_wbs", sa.Column("deliverables", sa.Text(), nullable=True))
    op.add_column("milestones_wbs", sa.Column("acceptance_conditions", sa.Text(), nullable=True))
    op.add_column("milestones_wbs", sa.Column("tvgs_checkpoint", sa.Text(), nullable=True))
    op.add_column("milestones_wbs", sa.Column("pm_comment", sa.Text(), nullable=True))

    risk_level = postgresql.ENUM(*RISK_LEVEL_VALUES, name="risk_level", create_type=False)
    risk_level.create(op.get_bind(), checkfirst=True)
    op.add_column("project_risks_and_issues", sa.Column("impact", risk_level, nullable=True))
    op.add_column("project_risks_and_issues", sa.Column("likelihood", risk_level, nullable=True))
    op.add_column(
        "project_risks_and_issues", sa.Column("coordinating_units", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("project_risks_and_issues", "coordinating_units")
    op.drop_column("project_risks_and_issues", "likelihood")
    op.drop_column("project_risks_and_issues", "impact")
    postgresql.ENUM(name="risk_level").drop(op.get_bind(), checkfirst=True)

    op.drop_column("milestones_wbs", "pm_comment")
    op.drop_column("milestones_wbs", "tvgs_checkpoint")
    op.drop_column("milestones_wbs", "acceptance_conditions")
    op.drop_column("milestones_wbs", "deliverables")
