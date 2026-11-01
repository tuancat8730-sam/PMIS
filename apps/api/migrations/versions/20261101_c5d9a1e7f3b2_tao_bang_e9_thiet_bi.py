"""tao bang e9 thiet bi

Revision ID: c5d9a1e7f3b2
Revises: c9e4a2f1b7d3
Create Date: 2026-11-01 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c5d9a1e7f3b2"
down_revision: str | None = "c9e4a2f1b7d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_equipment_catalog() -> None:
    op.create_table(
        "equipment_catalog",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("item_stt", sa.Integer(), nullable=True),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("item_name", sa.Text(), nullable=False),
        sa.Column("category_batch", sa.String(length=50), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("origin_country", sa.String(length=100), nullable=True),
        sa.Column("manufacture_year", sa.Integer(), nullable=True),
        sa.Column("contract_quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("technical_specs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "sample_approval_status",
            sa.String(length=50),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("sample_serial_number", sa.String(length=100), nullable=True),
        sa.Column(
            "sample_inspection_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "co_cq_status",
            sa.String(length=50),
            server_default=sa.text("'MISSING'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "contract_quantity >= 0", name="ck_equipment_catalog_quantity_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_equipment_catalog_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_catalog")),
        sa.UniqueConstraint(
            "project_id",
            "item_code",
            "category_batch",
            name="uq_equipment_catalog_project_item_batch",
        ),
    )
    op.create_index(
        op.f("ix_equipment_catalog_project_id"),
        "equipment_catalog",
        ["project_id"],
        unique=False,
    )


def _create_sample_inspections() -> None:
    op.create_table(
        "sample_inspections",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("inspected_on", sa.Date(), nullable=False),
        sa.Column("inspector", sa.String(length=150), nullable=False),
        sa.Column("serial_number_sample", sa.String(length=150), nullable=True),
        sa.Column("criteria_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("conclusion", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment_catalog.id"],
            name=op.f("fk_sample_inspections_equipment_id_equipment_catalog"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sample_inspections")),
    )
    op.create_index(
        op.f("ix_sample_inspections_equipment_id"),
        "sample_inspections",
        ["equipment_id"],
        unique=False,
    )


def _create_delivery_handovers() -> None:
    op.create_table(
        "delivery_handovers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("beneficiary_unit_id", sa.Uuid(), nullable=False),
        sa.Column("batch_code", sa.String(length=50), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=True),
        sa.Column("actual_date", sa.Date(), nullable=True),
        sa.Column(
            "delivery_status",
            sa.String(length=50),
            server_default=sa.text("'SCHEDULED'"),
            nullable=False,
        ),
        sa.Column("generated_docx_drive_id", sa.Uuid(), nullable=True),
        sa.Column("signed_scan_drive_id", sa.Uuid(), nullable=True),
        sa.Column(
            "site_photos",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("supervisor_name", sa.String(length=150), nullable=True),
        sa.Column("inspector_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_delivery_handovers_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["beneficiary_unit_id"],
            ["beneficiary_units.id"],
            name=op.f("fk_delivery_handovers_beneficiary_unit_id_beneficiary_units"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["generated_docx_drive_id"],
            ["drive_files.id"],
            name=op.f("fk_delivery_handovers_generated_docx_drive_id_drive_files"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["signed_scan_drive_id"],
            ["drive_files.id"],
            name=op.f("fk_delivery_handovers_signed_scan_drive_id_drive_files"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_handovers")),
        sa.UniqueConstraint(
            "project_id",
            "beneficiary_unit_id",
            "batch_code",
            name="uq_delivery_handovers_project_unit_batch",
        ),
    )
    op.create_index(
        op.f("ix_delivery_handovers_project_id"),
        "delivery_handovers",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_handovers_beneficiary_unit_id"),
        "delivery_handovers",
        ["beneficiary_unit_id"],
        unique=False,
    )


def _create_equipment_serials() -> None:
    op.create_table(
        "equipment_serials",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("beneficiary_unit_id", sa.Uuid(), nullable=True),
        sa.Column("handover_id", sa.Uuid(), nullable=True),
        sa.Column("serial_number_primary", sa.String(length=150), nullable=False),
        sa.Column("serial_number_secondary", sa.String(length=150), nullable=True),
        sa.Column("batch_lot_code", sa.String(length=100), nullable=True),
        sa.Column("co_cq_reference", sa.String(length=150), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=50),
            server_default=sa.text("'IMPORTED'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_equipment_serials_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment_catalog.id"],
            name=op.f("fk_equipment_serials_equipment_id_equipment_catalog"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["beneficiary_unit_id"],
            ["beneficiary_units.id"],
            name=op.f("fk_equipment_serials_beneficiary_unit_id_beneficiary_units"),
        ),
        sa.ForeignKeyConstraint(
            ["handover_id"],
            ["delivery_handovers.id"],
            name=op.f("fk_equipment_serials_handover_id_delivery_handovers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment_serials")),
        sa.UniqueConstraint(
            "project_id",
            "serial_number_primary",
            name="uq_equipment_serials_project_primary",
        ),
    )
    op.create_index(
        op.f("ix_equipment_serials_project_id"),
        "equipment_serials",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_serials_equipment_id"),
        "equipment_serials",
        ["equipment_id"],
        unique=False,
    )


def upgrade() -> None:
    _create_equipment_catalog()
    _create_sample_inspections()
    _create_delivery_handovers()
    _create_equipment_serials()


def downgrade() -> None:
    op.drop_index(op.f("ix_equipment_serials_equipment_id"), table_name="equipment_serials")
    op.drop_index(op.f("ix_equipment_serials_project_id"), table_name="equipment_serials")
    op.drop_table("equipment_serials")
    op.drop_index(
        op.f("ix_delivery_handovers_beneficiary_unit_id"), table_name="delivery_handovers"
    )
    op.drop_index(op.f("ix_delivery_handovers_project_id"), table_name="delivery_handovers")
    op.drop_table("delivery_handovers")
    op.drop_index(op.f("ix_sample_inspections_equipment_id"), table_name="sample_inspections")
    op.drop_table("sample_inspections")
    op.drop_index(op.f("ix_equipment_catalog_project_id"), table_name="equipment_catalog")
    op.drop_table("equipment_catalog")
