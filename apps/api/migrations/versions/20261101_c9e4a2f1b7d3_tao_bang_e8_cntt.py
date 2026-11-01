"""tao bang e8 cntt: phan he, khao sat, rtm, pentest, nfr; them resolution_ref cho risk_issues

Revision ID: c9e4a2f1b7d3
Revises: f7a1d3c9e2b4
Create Date: 2026-11-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c9e4a2f1b7d3"
down_revision: str | None = "f7a1d3c9e2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_it_system_modules() -> None:
    op.create_table(
        "it_system_modules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("module_code", sa.String(length=20), nullable=False),
        sa.Column("module_name", sa.Text(), nullable=False),
        sa.Column("responsible_contractor", sa.String(length=150), nullable=True),
        sa.Column(
            "dev_progress",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "internal_qa_status",
            sa.String(length=50),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "uat_status",
            sa.String(length=50),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "feature_checklist",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "nfr_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_it_system_modules_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_it_system_modules")),
        sa.UniqueConstraint("project_id", "module_code", name="uq_it_system_modules_project_code"),
    )
    op.create_index(
        op.f("ix_it_system_modules_project_id"),
        "it_system_modules",
        ["project_id"],
        unique=False,
    )


def _create_it_survey_records() -> None:
    op.create_table(
        "it_survey_records",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("unit_name", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'NOT_STARTED'"),
            nullable=False,
        ),
        sa.Column("survey_date", sa.Date(), nullable=True),
        sa.Column("minutes_document_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_it_survey_records_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["minutes_document_id"],
            ["legal_documents.id"],
            name=op.f("fk_it_survey_records_minutes_document_id_legal_documents"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_it_survey_records")),
        sa.UniqueConstraint("project_id", "unit_name", name="uq_it_survey_records_project_unit"),
    )
    op.create_index(
        op.f("ix_it_survey_records_project_id"),
        "it_survey_records",
        ["project_id"],
        unique=False,
    )


def _create_rtm_links() -> None:
    op.create_table(
        "rtm_links",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("appendix_c_ref", sa.String(length=100), nullable=True),
        sa.Column("srs_ref", sa.String(length=100), nullable=True),
        sa.Column("module_code", sa.String(length=20), nullable=True),
        sa.Column("test_case_ref", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_rtm_links_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rtm_links")),
    )
    op.create_index(op.f("ix_rtm_links_project_id"), "rtm_links", ["project_id"], unique=False)


def _create_pentest_findings() -> None:
    op.create_table(
        "pentest_findings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "fix_status",
            sa.String(length=20),
            server_default=sa.text("'OPEN'"),
            nullable=False,
        ),
        sa.Column("rechecked_on", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_pentest_findings_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pentest_findings")),
    )
    op.create_index(
        op.f("ix_pentest_findings_project_id"),
        "pentest_findings",
        ["project_id"],
        unique=False,
    )


def _create_nfr_measurements() -> None:
    op.create_table(
        "nfr_measurements",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("measured", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column(
            "measured_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_nfr_measurements_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by"],
            ["users.id"],
            name=op.f("fk_nfr_measurements_recorded_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nfr_measurements")),
    )
    op.create_index(
        op.f("ix_nfr_measurements_project_id"),
        "nfr_measurements",
        ["project_id"],
        unique=False,
    )


def upgrade() -> None:
    _create_it_system_modules()
    _create_it_survey_records()
    _create_rtm_links()
    _create_pentest_findings()
    _create_nfr_measurements()
    op.add_column("risk_issues", sa.Column("resolution_ref", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("risk_issues", "resolution_ref")
    op.drop_table("nfr_measurements")
    op.drop_table("pentest_findings")
    op.drop_table("rtm_links")
    op.drop_table("it_survey_records")
    op.drop_table("it_system_modules")
