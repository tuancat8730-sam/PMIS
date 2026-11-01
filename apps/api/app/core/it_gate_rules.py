"""Cổng hoàn thành mốc CNTT (thuần, không chạm DB).

Theo Q6: chỉ mốc M8 (Nghiệm thu) bị khóa. Điều kiện đủ gồm ba mục:
hồ sơ ATTT cấp độ 3 đã khóa, không còn lỗi pentest Critical/High chưa vá, và mọi chỉ tiêu NFR đạt.
"""

from collections.abc import Sequence

from app.core.nfr_rules import NfrResult, all_passed

GATED_MILESTONE_CODE = "M8"

DOSSIER_NOT_CLOSED_MESSAGE = "hồ sơ ATTT cấp độ 3 chưa ở trạng thái đã khóa"
PENTEST_OPEN_MESSAGE = "còn {count} lỗi pentest Critical/High chưa vá"
NFR_NOT_PASSED_MESSAGE = "chỉ tiêu NFR chưa đạt hoặc chưa có số đo"


def is_gated_milestone(milestone_code: str) -> bool:
    return milestone_code == GATED_MILESTONE_CODE


def it_completion_blockers(
    dossier_closed: bool,
    open_serious_pentest_count: int,
    nfr_results: Sequence[NfrResult],
) -> tuple[str, ...]:
    """Các lý do chặn hoàn thành mốc, viết tiếng Việt để trả cho người dùng. Rỗng là được phép."""
    blockers: list[str] = []
    if not dossier_closed:
        blockers.append(DOSSIER_NOT_CLOSED_MESSAGE)
    if open_serious_pentest_count > 0:
        blockers.append(PENTEST_OPEN_MESSAGE.format(count=open_serious_pentest_count))
    if not all_passed(nfr_results):
        blockers.append(NFR_NOT_PASSED_MESSAGE)
    return tuple(blockers)
