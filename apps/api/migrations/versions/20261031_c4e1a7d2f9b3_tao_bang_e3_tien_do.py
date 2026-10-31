"""tao bang e3 tien do

Revision ID: c4e1a7d2f9b3
Revises: 2a5dbfd319bf
Create Date: 2026-10-31 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e1a7d2f9b3"
down_revision: str | None = "2a5dbfd319bf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "milestones_wbs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("baseline_start", sa.Date(), nullable=True),
        sa.Column("baseline_end", sa.Date(), nullable=False),
        sa.Column("adjusted_start", sa.Date(), nullable=True),
        sa.Column("adjusted_end", sa.Date(), nullable=True),
        sa.Column("actual_end", sa.Date(), nullable=True),
        sa.Column(
            "is_hard_deadline", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "progress_percent",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("NOT_STARTED", "IN_PROGRESS", "COMPLETED", name="milestone_status"),
            server_default=sa.text("'NOT_STARTED'"),
            nullable=False,
        ),
        sa.Column("responsible_party", sa.Text(), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["milestones_wbs.id"],
            name=op.f("fk_milestones_wbs_parent_id_milestones_wbs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_milestones_wbs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milestones_wbs")),
        sa.UniqueConstraint("project_id", "code", name="uq_milestones_project_code"),
    )
    op.create_index(
        op.f("ix_milestones_wbs_project_id"), "milestones_wbs", ["project_id"], unique=False
    )

    op.create_table(
        "hold_points",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("milestone_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["milestone_id"],
            ["milestones_wbs.id"],
            name=op.f("fk_hold_points_milestone_id_milestones_wbs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_hold_points_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hold_points")),
        sa.UniqueConstraint("project_id", "code", name="uq_hold_points_project_code"),
    )
    op.create_index(
        op.f("ix_hold_points_milestone_id"), "hold_points", ["milestone_id"], unique=False
    )
    op.create_index(op.f("ix_hold_points_project_id"), "hold_points", ["project_id"], unique=False)

    op.create_table(
        "hold_point_confirmations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("hold_point_id", sa.Uuid(), nullable=False),
        sa.Column(
            "party",
            sa.Enum("CDT", "TVGS", "NHA_THAU", name="confirming_party"),
            nullable=False,
        ),
        sa.Column("confirmed_by", sa.Uuid(), nullable=False),
        sa.Column("evidence_ref", sa.Text(), nullable=False),
        sa.Column(
            "confirmed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["users.id"],
            name=op.f("fk_hold_point_confirmations_confirmed_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["hold_point_id"],
            ["hold_points.id"],
            name=op.f("fk_hold_point_confirmations_hold_point_id_hold_points"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hold_point_confirmations")),
        sa.UniqueConstraint("hold_point_id", "party", name="uq_hold_point_confirmations_party"),
    )
    op.create_index(
        op.f("ix_hold_point_confirmations_hold_point_id"),
        "hold_point_confirmations",
        ["hold_point_id"],
        unique=False,
    )

    op.create_table(
        "milestone_adjustments",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("milestone_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("previous_end", sa.Date(), nullable=False),
        sa.Column("new_end", sa.Date(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_milestone_adjustments_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["milestone_id"],
            ["milestones_wbs.id"],
            name=op.f("fk_milestone_adjustments_milestone_id_milestones_wbs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milestone_adjustments")),
    )
    op.create_index(
        op.f("ix_milestone_adjustments_milestone_id"),
        "milestone_adjustments",
        ["milestone_id"],
        unique=False,
    )

    op.create_table(
        "penalty_rules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("rate_per_day", sa.Numeric(precision=7, scale=6), nullable=False),
        sa.Column("cap_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_penalty_rules_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_penalty_rules")),
        sa.UniqueConstraint(
            "project_id", "effective_from", name="uq_penalty_rules_project_effective"
        ),
    )
    op.create_index(
        op.f("ix_penalty_rules_project_id"), "penalty_rules", ["project_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_penalty_rules_project_id"), table_name="penalty_rules")
    op.drop_table("penalty_rules")
    op.drop_index(op.f("ix_milestone_adjustments_milestone_id"), table_name="milestone_adjustments")
    op.drop_table("milestone_adjustments")
    op.drop_index(
        op.f("ix_hold_point_confirmations_hold_point_id"), table_name="hold_point_confirmations"
    )
    op.drop_table("hold_point_confirmations")
    op.drop_index(op.f("ix_hold_points_project_id"), table_name="hold_points")
    op.drop_index(op.f("ix_hold_points_milestone_id"), table_name="hold_points")
    op.drop_table("hold_points")
    op.drop_index(op.f("ix_milestones_wbs_project_id"), table_name="milestones_wbs")
    op.drop_table("milestones_wbs")
    # Autogenerate không tự xóa enum; phải xóa tay để downgrade rồi upgrade lại không lỗi.
    sa.Enum(name="confirming_party").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="milestone_status").drop(op.get_bind(), checkfirst=True)
