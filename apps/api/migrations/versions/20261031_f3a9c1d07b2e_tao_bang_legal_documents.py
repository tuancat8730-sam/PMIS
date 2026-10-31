"""tao bang legal_documents (E4 checklist phap ly)

Revision ID: f3a9c1d07b2e
Revises: e8b2c5f1a3d4
Create Date: 2026-10-31 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a9c1d07b2e"
down_revision: str | None = "e8b2c5f1a3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DOC_MATURITY_VALUES = (
    "MISSING",
    "DRAFT_DOCX",
    "SUBMITTED_REVIEW",
    "WAITING_SIGNATURE",
    "SIGNED_SCAN_PDF",
    "DISCREPANCY_FOUND",
    "VERIFIED_CLOSED",
)
PHASE_GROUP_VALUES = (
    "PREPARATION",
    "BIDDING",
    "CONTRACT_KICKOFF",
    "IMPLEMENTATION",
    "ACCEPTANCE",
)


def upgrade() -> None:
    op.create_table(
        "legal_documents",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("stt", sa.Integer(), nullable=True),
        sa.Column(
            "phase_group",
            sa.Enum(*PHASE_GROUP_VALUES, name="legal_phase_group"),
            nullable=False,
        ),
        sa.Column("doc_code_symbol", sa.String(length=100), nullable=True),
        sa.Column("doc_name", sa.Text(), nullable=False),
        sa.Column("issuing_authority", sa.String(length=150), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "maturity_status",
            sa.Enum(*DOC_MATURITY_VALUES, name="doc_maturity_status"),
            server_default=sa.text("'MISSING'"),
            nullable=False,
        ),
        sa.Column("pm_action_required", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.String(length=150), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_legal_documents_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_legal_documents")),
        sa.UniqueConstraint("project_id", "stt", name="uq_legal_documents_project_stt"),
    )
    op.create_index(
        op.f("ix_legal_documents_project_id"),
        "legal_documents",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_legal_documents_project_id"), table_name="legal_documents")
    op.drop_table("legal_documents")
    # Autogenerate không tự xóa enum; phải xóa tay để downgrade rồi upgrade lại không lỗi.
    bind = op.get_bind()
    for enum_name in ("doc_maturity_status", "legal_phase_group"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
