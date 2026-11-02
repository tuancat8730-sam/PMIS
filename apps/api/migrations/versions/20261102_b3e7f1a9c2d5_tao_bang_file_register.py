"""tao bang project_file_register (Pha 3 tracking: quan ly file va bang chung)

Revision ID: b3e7f1a9c2d5
Revises: a1c4e8f2b9d3
Create Date: 2026-11-02 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3e7f1a9c2d5"
down_revision: str | None = "a1c4e8f2b9d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_file_register",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("stt", sa.Integer(), nullable=False),
        sa.Column("folder_path", sa.Text(), nullable=True),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_format", sa.String(length=50), nullable=True),
        sa.Column("storage_location", sa.String(length=100), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("legal_status", sa.Text(), nullable=True),
        sa.Column("security_ownership", sa.String(length=150), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("drive_file_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_file_register_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["drive_file_id"],
            ["drive_files.id"],
            name=op.f("fk_project_file_register_drive_file_id_drive_files"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_file_register")),
        sa.UniqueConstraint("project_id", "stt", name="uq_project_file_register_stt"),
    )
    op.create_index(
        op.f("ix_project_file_register_project_id"),
        "project_file_register",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_project_file_register_project_id"), table_name="project_file_register")
    op.drop_table("project_file_register")
