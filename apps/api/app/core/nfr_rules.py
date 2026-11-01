"""Chỉ tiêu phi chức năng (NFR) thuần: so số đo với ngưỡng, không chạm DB.

Ngưỡng do người gọi truyền vào (lấy từ `it_system_modules.nfr_metrics`), không hard-code ở đây.
Thiếu số đo thì coi là không đạt: không có bằng chứng thì không nghiệm thu.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any


class Comparison(StrEnum):
    AT_LEAST = "AT_LEAST"  # số đo >= ngưỡng
    AT_MOST = "AT_MOST"  # số đo <= ngưỡng
    BELOW = "BELOW"  # số đo < ngưỡng (nghiêm ngặt)


@dataclass(frozen=True)
class NfrCriterion:
    key: str
    comparison: Comparison
    threshold: Decimal


@dataclass(frozen=True)
class NfrResult:
    key: str
    passed: bool
    measured: Decimal | None


def meets(measured: Decimal, criterion: NfrCriterion) -> bool:
    """Số đo có đạt chỉ tiêu không, theo đúng kiểu so sánh."""
    if criterion.comparison is Comparison.AT_LEAST:
        return measured >= criterion.threshold
    if criterion.comparison is Comparison.AT_MOST:
        return measured <= criterion.threshold
    return measured < criterion.threshold


def evaluate_nfr(
    criteria: Iterable[NfrCriterion],
    measurements: Mapping[str, Decimal],
) -> tuple[NfrResult, ...]:
    """Đánh giá từng chỉ tiêu theo thứ tự đầu vào; thiếu số đo thì không đạt."""
    return tuple(_evaluate_one(criterion, measurements) for criterion in criteria)


def criteria_from_json(raw: Mapping[str, Mapping[str, Any]]) -> tuple[NfrCriterion, ...]:
    """Đọc ngưỡng từ JSONB `nfr_metrics`; dữ liệu sai thì báo ValueError, không đoán giá trị."""
    return tuple(_criterion_from_spec(key, spec) for key, spec in raw.items())


def _criterion_from_spec(key: str, spec: Mapping[str, Any]) -> NfrCriterion:
    try:
        comparison = Comparison(spec["comparison"])
        threshold = Decimal(str(spec["threshold"]))
    except (KeyError, ValueError, ArithmeticError) as exc:
        raise ValueError(f"Ngưỡng NFR '{key}' không hợp lệ") from exc
    return NfrCriterion(key=key, comparison=comparison, threshold=threshold)


def all_passed(results: Iterable[NfrResult]) -> bool:
    """Cổng đạt khi có ít nhất một chỉ tiêu và mọi chỉ tiêu đều đạt."""
    materialized = tuple(results)
    return bool(materialized) and all(result.passed for result in materialized)


def _evaluate_one(
    criterion: NfrCriterion,
    measurements: Mapping[str, Decimal],
) -> NfrResult:
    measured = measurements.get(criterion.key)
    if measured is None:
        return NfrResult(key=criterion.key, passed=False, measured=None)
    return NfrResult(
        key=criterion.key,
        passed=meets(measured, criterion),
        measured=measured,
    )
