from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.nfr_rules import criteria_from_json
from app.db.seed_it_system import HCM_NFR_CRITERIA
from app.schemas.it_system import ModuleCreate, ModuleUpdate, PentestUpdate, SurveyUpdate

pytestmark = pytest.mark.unit


def test_module_create_rejects_unknown_nfr_comparison() -> None:
    # Arrange
    raw = {
        "module_code": "A",
        "module_name": "Phân hệ A",
        "nfr_metrics": {"ccu": {"comparison": "EQUALS", "threshold": "3600"}},
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        ModuleCreate(**raw)


def test_module_create_rejects_progress_above_100() -> None:
    # Arrange
    raw = {"module_code": "A", "module_name": "Phân hệ A", "dev_progress": Decimal("101")}

    # Act / Assert
    with pytest.raises(ValidationError):
        ModuleCreate(**raw)


def test_module_update_rejects_null_qa_status() -> None:
    # Arrange
    raw = {"internal_qa_status": None}

    # Act / Assert
    with pytest.raises(ValidationError):
        ModuleUpdate(**raw)


def test_module_update_allows_omitting_fields() -> None:
    # Arrange / Act
    payload = ModuleUpdate(dev_progress=Decimal("42.5"))

    # Assert
    assert payload.model_dump(exclude_unset=True) == {"dev_progress": Decimal("42.5")}


def test_survey_update_rejects_null_status() -> None:
    # Arrange
    raw = {"status": None}

    # Act / Assert
    with pytest.raises(ValidationError):
        SurveyUpdate(**raw)


def test_pentest_update_rejects_unknown_fix_status() -> None:
    # Arrange
    raw = {"fix_status": "DONE"}

    # Act / Assert
    with pytest.raises(ValidationError):
        PentestUpdate(**raw)


def test_seed_nfr_criteria_cover_all_nine_spec_metrics() -> None:
    # Arrange
    raw = HCM_NFR_CRITERIA

    # Act
    criteria = criteria_from_json(raw)

    # Assert
    assert len(criteria) == 9
    assert {criterion.key for criterion in criteria} >= {"ccu", "uptime_percent", "rto_hours"}
