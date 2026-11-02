"""tao bang chi phi, yeu cau ky thuat va cot tong quan hop dong (tab Tong quan)

Revision ID: a7d3e9f2c1b8
Revises: e6a0c4b8d2f7
Create Date: 2026-11-02 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7d3e9f2c1b8"
down_revision: str | None = "e6a0c4b8d2f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BUDGET_CATEGORY_VALUES = (
    "SOFTWARE",
    "PROJECT_MANAGEMENT",
    "CONSULTING",
    "OTHER",
    "CONTINGENCY",
)


def upgrade() -> None:
    budget_category = postgresql.ENUM(
        *BUDGET_CATEGORY_VALUES, name="budget_category", create_type=False
    )
    budget_category.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "project_budget_items",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("category", budget_category, nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_budget_items_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_budget_items")),
        sa.UniqueConstraint("project_id", "category", name="uq_project_budget_items_category"),
    )
    op.create_index(
        op.f("ix_project_budget_items_project_id"),
        "project_budget_items",
        ["project_id"],
        unique=False,
    )

    op.create_table(
        "project_technical_requirements",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column("standard", sa.Text(), nullable=True),
        sa.Column("legal_basis", sa.Text(), nullable=True),
        sa.Column("solution", sa.Text(), nullable=True),
        sa.Column("responsibility", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.Text(), nullable=True),
        sa.Column("related_risk", sa.Text(), nullable=True),
        sa.Column("monitoring_status", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_technical_requirements_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_technical_requirements")),
        sa.UniqueConstraint("project_id", "item", name="uq_project_technical_requirements_item"),
    )
    op.create_index(
        op.f("ix_project_technical_requirements_project_id"),
        "project_technical_requirements",
        ["project_id"],
        unique=False,
    )

    op.add_column("contracts", sa.Column("contractor_name", sa.Text(), nullable=True))
    op.add_column("contracts", sa.Column("role_label", sa.String(length=100), nullable=True))
    op.add_column("contracts", sa.Column("contact_person", sa.Text(), nullable=True))
    op.add_column("contracts", sa.Column("status_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("contracts", "status_note")
    op.drop_column("contracts", "contact_person")
    op.drop_column("contracts", "role_label")
    op.drop_column("contracts", "contractor_name")

    op.drop_index(
        op.f("ix_project_technical_requirements_project_id"),
        table_name="project_technical_requirements",
    )
    op.drop_table("project_technical_requirements")

    op.drop_index(op.f("ix_project_budget_items_project_id"), table_name="project_budget_items")
    op.drop_table("project_budget_items")
    postgresql.ENUM(name="budget_category").drop(op.get_bind(), checkfirst=True)
