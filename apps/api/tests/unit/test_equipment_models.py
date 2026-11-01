import pytest
from sqlalchemy import UniqueConstraint

from app.db.base import Base
from app.models import (
    DeliveryHandover,
    EquipmentCatalog,
    EquipmentSerial,
    SampleInspection,
)

pytestmark = pytest.mark.unit


def _unique_column_sets(table_name: str) -> set[frozenset[str]]:
    table = Base.metadata.tables[table_name]
    return {
        frozenset(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def test_equipment_catalog_is_unique_per_project_item_code_and_batch() -> None:
    # Arrange / Act
    unique_sets = _unique_column_sets(EquipmentCatalog.__tablename__)

    # Assert
    assert frozenset({"project_id", "item_code", "category_batch"}) in unique_sets


def test_serial_number_is_unique_per_project() -> None:
    # Arrange / Act
    unique_sets = _unique_column_sets(EquipmentSerial.__tablename__)

    # Assert
    assert frozenset({"project_id", "serial_number_primary"}) in unique_sets


def test_handover_is_unique_per_project_unit_and_batch() -> None:
    # Arrange / Act
    unique_sets = _unique_column_sets(DeliveryHandover.__tablename__)

    # Assert
    assert frozenset({"project_id", "beneficiary_unit_id", "batch_code"}) in unique_sets


def test_sample_inspection_stores_criteria_results_as_jsonb() -> None:
    # Arrange
    table = Base.metadata.tables[SampleInspection.__tablename__]

    # Act
    column_type = table.c.criteria_results.type

    # Assert
    assert column_type.__class__.__name__ == "JSONB"


def test_equipment_tables_use_expected_names() -> None:
    # Arrange / Act / Assert
    assert EquipmentCatalog.__tablename__ == "equipment_catalog"
    assert SampleInspection.__tablename__ == "sample_inspections"
    assert EquipmentSerial.__tablename__ == "equipment_serials"
    assert DeliveryHandover.__tablename__ == "delivery_handovers"
