"""Ma trận truy vết (RTM) thuần: tìm mắt xích thiếu trong chuỗi Phụ lục C → SRS → phân hệ → test.

Mỗi dòng là một chuỗi bốn mắt xích dạng mã chuỗi. Mắt xích rỗng hoặc chỉ có khoảng trắng là mồ côi.
"""

from dataclasses import dataclass

LINK_APPENDIX_C = "appendix_c_ref"
LINK_SRS = "srs_ref"
LINK_MODULE = "module_code"
LINK_TEST_CASE = "test_case_ref"


@dataclass(frozen=True)
class RtmRow:
    appendix_c_ref: str | None
    srs_ref: str | None
    module_code: str | None
    test_case_ref: str | None


def missing_chain_links(row: RtmRow) -> frozenset[str]:
    """Tên các mắt xích rỗng hoặc chỉ có khoảng trắng trong một dòng."""
    links = {
        LINK_APPENDIX_C: row.appendix_c_ref,
        LINK_SRS: row.srs_ref,
        LINK_MODULE: row.module_code,
        LINK_TEST_CASE: row.test_case_ref,
    }
    return frozenset(name for name, value in links.items() if not _is_filled(value))


def orphan_rows(rows: tuple[RtmRow, ...]) -> tuple[tuple[int, frozenset[str]], ...]:
    """Các dòng còn mắt xích thiếu, kèm chỉ số dòng và tên mắt xích thiếu."""
    return tuple(
        (index, missing) for index, row in enumerate(rows) if (missing := missing_chain_links(row))
    )


def _is_filled(value: str | None) -> bool:
    return value is not None and value.strip() != ""
