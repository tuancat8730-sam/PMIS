"""tao bang project_legal_decisions (Pha 4 tracking: tong quan du an)

Revision ID: c4f8a2d6e1b9
Revises: b3e7f1a9c2d5
Create Date: 2026-11-02 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4f8a2d6e1b9"
down_revision: str | None = "b3e7f1a9c2d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGAL_DECISION_KIND_VALUES = (
    "PROJECT_APPROVAL",
    "BCKTKT_APPROVAL",
    "BUDGET_APPROVAL",
    "KHLCNT_APPROVAL",
    "BIDDING_RESULT_APPROVAL",
    "SUPERVISION_ASSIGNMENT",
)


def upgrade() -> None:
    legal_decision_kind = postgresql.ENUM(
        *LEGAL_DECISION_KIND_VALUES, name="legal_decision_kind", create_type=False
    )
    legal_decision_kind.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "project_legal_decisions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("kind", legal_decision_kind, nullable=False),
        sa.Column("decision_no", sa.String(length=100), nullable=False),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(length=150), nullable=True),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("funding_source", sa.Text(), nullable=True),
        sa.Column("execution_period", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_legal_decisions_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_legal_decisions")),
        sa.UniqueConstraint("project_id", "decision_no", name="uq_project_legal_decisions_no"),
    )
    op.create_index(
        op.f("ix_project_legal_decisions_project_id"),
        "project_legal_decisions",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_project_legal_decisions_project_id"), table_name="project_legal_decisions"
    )
    op.drop_table("project_legal_decisions")
    postgresql.ENUM(name="legal_decision_kind").drop(op.get_bind(), checkfirst=True)
