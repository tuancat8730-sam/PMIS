"""tao bang drive_files va FK file Drive trong legal_documents (E5 Google Drive)

Revision ID: a7d3e9b1c5f2
Revises: f3a9c1d07b2e
Create Date: 2026-11-01 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7d3e9b1c5f2"
down_revision: str | None = "f3a9c1d07b2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drive_files",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("drive_file_id", sa.String(length=128), nullable=False),
        sa.Column("drive_parent_id", sa.String(length=128), nullable=True),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("drive_path", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(length=150), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("web_view_link", sa.Text(), nullable=True),
        sa.Column("modified_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("has_signature_or_stamp", sa.Boolean(), nullable=True),
        sa.Column(
            "ai_audit_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "last_synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_drive_files_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drive_files")),
        sa.UniqueConstraint("drive_file_id", name=op.f("uq_drive_files_drive_file_id")),
    )
    op.create_index(op.f("ix_drive_files_project_id"), "drive_files", ["project_id"], unique=False)
    op.add_column("legal_documents", sa.Column("draft_drive_file_id", sa.Uuid(), nullable=True))
    op.add_column("legal_documents", sa.Column("signed_drive_file_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_legal_documents_draft_drive_file_id_drive_files"),
        "legal_documents",
        "drive_files",
        ["draft_drive_file_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_legal_documents_signed_drive_file_id_drive_files"),
        "legal_documents",
        "drive_files",
        ["signed_drive_file_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Xóa FK trước rồi mới xóa cột và bảng, theo thứ tự phụ thuộc.
    op.drop_constraint(
        op.f("fk_legal_documents_signed_drive_file_id_drive_files"),
        "legal_documents",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_legal_documents_draft_drive_file_id_drive_files"),
        "legal_documents",
        type_="foreignkey",
    )
    op.drop_column("legal_documents", "signed_drive_file_id")
    op.drop_column("legal_documents", "draft_drive_file_id")
    op.drop_index(op.f("ix_drive_files_project_id"), table_name="drive_files")
    op.drop_table("drive_files")
