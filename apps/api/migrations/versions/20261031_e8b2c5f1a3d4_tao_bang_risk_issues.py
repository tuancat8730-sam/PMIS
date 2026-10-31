"""tao bang project risks and issues

Revision ID: e8b2c5f1a3d4
Revises: c4e1a7d2f9b3
Create Date: 2026-10-31 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8b2c5f1a3d4"
down_revision: str | None = "c4e1a7d2f9b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_risks_and_issues",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column(
            "record_type",
            sa.Enum("RISK", "ISSUE", "CR", "NCR", "CONTRACT_DISCREPANCY", name="risk_record_type"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum("CRITICAL", "HIGH", "MEDIUM", "LOW", name="risk_priority"),
            server_default=sa.text("'HIGH'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "IN_PROGRESS",
                "WAITING_INVESTOR",
                "RESOLVED",
                "CLOSED",
                name="risk_status",
            ),
            server_default=sa.text("'OPEN'"),
            nullable=False,
        ),
        sa.Column("target_stakeholder", sa.String(length=100), nullable=True),
        sa.Column("mitigation_action", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=150), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_risks_and_issues_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_risks_and_issues")),
        sa.UniqueConstraint("project_id", "code", name="uq_risk_issues_project_code"),
    )
    op.create_index(
        op.f("ix_project_risks_and_issues_project_id"),
        "project_risks_and_issues",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_project_risks_and_issues_project_id"), table_name="project_risks_and_issues"
    )
    op.drop_table("project_risks_and_issues")
    # Autogenerate không tự xóa enum; phải xóa tay để downgrade rồi upgrade lại không lỗi.
    sa.Enum(name="risk_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="risk_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="risk_record_type").drop(op.get_bind(), checkfirst=True)
