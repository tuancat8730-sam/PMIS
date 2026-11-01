"""Kết luận kiểm định hàng mẫu theo tiêu chí kỹ thuật (thuần, không chạm DB).

Danh sách tiêu chí và số lượng do hợp đồng quy định, người gọi truyền vào `expected_count`.
Không hard-code số 21 ở đây (Q4 trong plan E9 chưa chốt danh sách).
"""

from collections.abc import Sequence
from dataclasses import dataclass

RESULT_PASSED = "ĐẠT"
RESULT_FAILED = "KHÔNG ĐẠT"
CONCLUSION_PASSED = "ĐẠT"
CONCLUSION_REWORK = "YÊU CẦU LÀM LẠI MẪU"

_VALID_RESULTS = frozenset({RESULT_PASSED, RESULT_FAILED})


class SampleInspectionError(Exception):
    """Dữ liệu kiểm định không hợp lệ: thiếu, trùng hoặc sai kết quả tiêu chí."""


@dataclass(frozen=True)
class CriterionResult:
    code: str
    result: str

    def __post_init__(self) -> None:
        if self.result not in _VALID_RESULTS:
            raise SampleInspectionError(
                f"Kết quả tiêu chí không hợp lệ: {self.result!r} (mã {self.code})"
            )


@dataclass(frozen=True)
class SampleVerdict:
    conclusion: str
    failed_codes: tuple[str, ...]


def _ensure_complete(criteria: Sequence[CriterionResult], expected_count: int) -> None:
    if len(criteria) != expected_count:
        raise SampleInspectionError(f"Thiếu tiêu chí: cần {expected_count}, nhận {len(criteria)}")
    codes = [criterion.code for criterion in criteria]
    if len(set(codes)) != len(codes):
        raise SampleInspectionError("Trùng mã tiêu chí trong phiếu kiểm định")


def evaluate_sample(
    criteria: Sequence[CriterionResult],
    *,
    expected_count: int,
) -> SampleVerdict:
    """Một tiêu chí KHÔNG ĐẠT thì mẫu phải làm lại; mọi tiêu chí ĐẠT thì mẫu được chấp nhận."""
    _ensure_complete(criteria, expected_count)
    failed_codes = tuple(
        criterion.code for criterion in criteria if criterion.result == RESULT_FAILED
    )
    conclusion = CONCLUSION_REWORK if failed_codes else CONCLUSION_PASSED
    return SampleVerdict(conclusion=conclusion, failed_codes=failed_codes)


APPROVAL_APPROVED = "APPROVED"
APPROVAL_REWORK_REQUIRED = "REWORK_REQUIRED"

_APPROVAL_BY_CONCLUSION = {
    CONCLUSION_PASSED: APPROVAL_APPROVED,
    CONCLUSION_REWORK: APPROVAL_REWORK_REQUIRED,
}


def approval_status_for(conclusion: str) -> str:
    """Trạng thái phê duyệt mẫu trên dòng mã hàng, suy ra từ kết luận kiểm định."""
    if conclusion not in _APPROVAL_BY_CONCLUSION:
        raise ValueError(f"Kết luận không xác định: {conclusion!r}")
    return _APPROVAL_BY_CONCLUSION[conclusion]


def ensure_codes_match_catalog(submitted: Sequence[str], catalog: Sequence[str]) -> None:
    """Phiếu kiểm định phải chứa đúng các mã tiêu chí của danh mục, không thiếu và không thừa."""
    if set(submitted) != set(catalog):
        raise SampleInspectionError("Mã tiêu chí không khớp danh mục")
