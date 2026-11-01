"""tao bang e7 tai chinh

Revision ID: f7a1d3c9e2b4
Revises: e8b2c5f1a3d4
Create Date: 2026-11-01 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a1d3c9e2b4"
down_revision: str | None = "e8b2c5f1a3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column(
            "package_kind",
            sa.String(length=20),
            server_default=sa.text("'MAIN'"),
            nullable=False,
        ),
    )

    op.create_table(
        "finance_rules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("guarantee_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("advance_ceiling_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("advance_working_days", sa.Integer(), nullable=False),
        sa.Column("lock_on", sa.Date(), nullable=False),
        sa.Column("lock_warning_days", sa.Integer(), nullable=False),
        sa.Column(
            "non_working_days",
            sa.ARRAY(sa.Date()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_finance_rules_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_finance_rules")),
        sa.UniqueConstraint(
            "project_id", "effective_from", name="uq_finance_rules_project_effective"
        ),
    )
    op.create_index(
        op.f("ix_finance_rules_project_id"), "finance_rules", ["project_id"], unique=False
    )

    op.create_table(
        "contract_guarantees",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("base_contract_value", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("poa_expires_on", sa.Date(), nullable=True),
        sa.CheckConstraint("amount >= 0", name="ck_contract_guarantees_amount_nonnegative"),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["contracts.id"],
            name=op.f("fk_contract_guarantees_contract_id_contracts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contract_guarantees")),
    )
    op.create_index(
        op.f("ix_contract_guarantees_contract_id"),
        "contract_guarantees",
        ["contract_id"],
        unique=False,
    )

    op.create_table(
        "contract_advances",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("complete_packet_on", sa.Date(), nullable=False),
        sa.Column("decided_on", sa.Date(), nullable=False),
        sa.Column("on_time", sa.Boolean(), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_contract_advances_amount_nonnegative"),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["contracts.id"],
            name=op.f("fk_contract_advances_contract_id_contracts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contract_advances")),
    )
    op.create_index(
        op.f("ix_contract_advances_contract_id"),
        "contract_advances",
        ["contract_id"],
        unique=False,
    )

    op.create_table(
        "disbursements",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("plan_year", sa.Integer(), nullable=False),
        sa.Column("planned_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "paid_amount",
            sa.Numeric(precision=18, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("paid_on", sa.Date(), nullable=True),
        sa.Column(
            "packet_status",
            sa.String(length=20),
            server_default=sa.text("'NOT_STARTED'"),
            nullable=False,
        ),
        sa.CheckConstraint("planned_amount >= 0", name="ck_disbursements_planned_nonnegative"),
        sa.CheckConstraint("paid_amount >= 0", name="ck_disbursements_paid_nonnegative"),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["contracts.id"],
            name=op.f("fk_disbursements_contract_id_contracts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_disbursements_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_disbursements")),
        sa.UniqueConstraint("contract_id", "plan_year", name="uq_disbursements_contract_year"),
    )
    op.create_index(
        op.f("ix_disbursements_contract_id"), "disbursements", ["contract_id"], unique=False
    )
    op.create_index(
        op.f("ix_disbursements_project_id"), "disbursements", ["project_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_disbursements_project_id"), table_name="disbursements")
    op.drop_index(op.f("ix_disbursements_contract_id"), table_name="disbursements")
    op.drop_table("disbursements")
    op.drop_index(op.f("ix_contract_advances_contract_id"), table_name="contract_advances")
    op.drop_table("contract_advances")
    op.drop_index(op.f("ix_contract_guarantees_contract_id"), table_name="contract_guarantees")
    op.drop_table("contract_guarantees")
    op.drop_index(op.f("ix_finance_rules_project_id"), table_name="finance_rules")
    op.drop_table("finance_rules")
    op.drop_column("contracts", "package_kind")
