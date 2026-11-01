import pytest

from app.core.sample_criteria import (
    CONCLUSION_PASSED,
    CONCLUSION_REWORK,
    RESULT_FAILED,
    RESULT_PASSED,
    CriterionResult,
    SampleInspectionError,
    evaluate_sample,
)

pytestmark = pytest.mark.unit

CRITERIA_COUNT = 21


def _criteria(
    count: int = CRITERIA_COUNT,
    failed_codes: frozenset[str] = frozenset(),
) -> list[CriterionResult]:
    return [
        CriterionResult(
            code=f"TC{index:02d}",
            result=RESULT_FAILED if f"TC{index:02d}" in failed_codes else RESULT_PASSED,
        )
        for index in range(1, count + 1)
    ]


def test_sample_passes_when_all_criteria_are_passed() -> None:
    # Arrange
    criteria = _criteria()

    # Act
    verdict = evaluate_sample(criteria, expected_count=CRITERIA_COUNT)

    # Assert
    assert verdict.conclusion == CONCLUSION_PASSED
    assert verdict.failed_codes == ()


def test_sample_requires_rework_when_one_criterion_fails() -> None:
    # Arrange
    criteria = _criteria(failed_codes=frozenset({"TC07"}))

    # Act
    verdict = evaluate_sample(criteria, expected_count=CRITERIA_COUNT)

    # Assert
    assert verdict.conclusion == CONCLUSION_REWORK
    assert verdict.failed_codes == ("TC07",)


def test_failed_codes_keep_input_order_when_several_criteria_fail() -> None:
    # Arrange
    criteria = _criteria(failed_codes=frozenset({"TC03", "TC19"}))

    # Act
    verdict = evaluate_sample(criteria, expected_count=CRITERIA_COUNT)

    # Assert
    assert verdict.failed_codes == ("TC03", "TC19")


def test_sample_is_rejected_when_fewer_criteria_than_contract_requires() -> None:
    # Arrange
    criteria = _criteria(count=CRITERIA_COUNT - 1)

    # Act / Assert
    with pytest.raises(SampleInspectionError, match="Thiếu tiêu chí"):
        evaluate_sample(criteria, expected_count=CRITERIA_COUNT)


def test_sample_is_rejected_when_a_criterion_code_is_duplicated() -> None:
    # Arrange
    criteria = [
        *_criteria(count=CRITERIA_COUNT - 1),
        CriterionResult(code="TC01", result=RESULT_PASSED),
    ]

    # Act / Assert
    with pytest.raises(SampleInspectionError, match="Trùng mã tiêu chí"):
        evaluate_sample(criteria, expected_count=CRITERIA_COUNT)


def test_criterion_result_must_be_passed_or_failed() -> None:
    # Arrange / Act / Assert
    with pytest.raises(SampleInspectionError, match="Kết quả tiêu chí không hợp lệ"):
        CriterionResult(code="TC01", result="CÓ THỂ")


def test_evaluate_sample_does_not_mutate_input_list() -> None:
    # Arrange
    criteria = _criteria(failed_codes=frozenset({"TC02"}))
    snapshot = list(criteria)

    # Act
    evaluate_sample(criteria, expected_count=CRITERIA_COUNT)

    # Assert
    assert criteria == snapshot
