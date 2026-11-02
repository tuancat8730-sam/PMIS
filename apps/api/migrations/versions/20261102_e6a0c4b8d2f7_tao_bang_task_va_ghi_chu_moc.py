"""tao bang milestone_tasks va milestone_notes (E3 tien do: task con va nhat ky ghi chu cua moc)

Revision ID: e6a0c4b8d2f7
Revises: d5e9b3a7f1c2
Create Date: 2026-11-02 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6a0c4b8d2f7"
down_revision: str | None = "d5e9b3a7f1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TASK_STATUS_VALUES = ("NOT_STARTED", "IN_PROGRESS", "COMPLETED")


def upgrade() -> None:
    task_status = postgresql.ENUM(
        *TASK_STATUS_VALUES, name="milestone_task_status", create_type=False
    )
    task_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "milestone_tasks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("milestone_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("status", task_status, server_default=sa.text("'NOT_STARTED'"), nullable=False),
        sa.Column("assignee", sa.String(length=300), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["milestone_id"],
            ["milestones_wbs.id"],
            name=op.f("fk_milestone_tasks_milestone_id_milestones_wbs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milestone_tasks")),
    )
    op.create_index(
        op.f("ix_milestone_tasks_milestone_id"), "milestone_tasks", ["milestone_id"], unique=False
    )

    op.create_table(
        "milestone_notes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("milestone_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["milestone_id"],
            ["milestones_wbs.id"],
            name=op.f("fk_milestone_notes_milestone_id_milestones_wbs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_milestone_notes_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milestone_notes")),
    )
    op.create_index(
        op.f("ix_milestone_notes_milestone_id"), "milestone_notes", ["milestone_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_milestone_notes_milestone_id"), table_name="milestone_notes")
    op.drop_table("milestone_notes")
    op.drop_index(op.f("ix_milestone_tasks_milestone_id"), table_name="milestone_tasks")
    op.drop_table("milestone_tasks")
    postgresql.ENUM(name="milestone_task_status").drop(op.get_bind(), checkfirst=True)
