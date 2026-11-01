"""Danh mục 21 tiêu chí kiểm định hàng mẫu (cấu hình, không chứa logic).

LƯU Ý: đây là danh sách TẠM do đội phát triển tự soạn theo ví dụ trong spec Phân hệ 6
(ký mã hiệu, hãng, xuất xứ, ISO/RoHS, CPU/RAM/SSD, HĐH bản quyền, bảo hành...).
Phải thay bằng danh sách lấy từ phụ lục bảng giá hợp đồng khi người dùng gửi (Q4 plan E9).
Thay đổi danh sách không cần sửa logic, vì `evaluate_sample` nhận số lượng từ đây.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleCriterion:
    code: str
    label: str


SAMPLE_CRITERIA: tuple[SampleCriterion, ...] = (
    SampleCriterion("TC01", "Ký mã hiệu"),
    SampleCriterion("TC02", "Hãng sản xuất"),
    SampleCriterion("TC03", "Xuất xứ"),
    SampleCriterion("TC04", "Năm sản xuất"),
    SampleCriterion("TC05", "Chứng chỉ ISO"),
    SampleCriterion("TC06", "Chứng chỉ RoHS"),
    SampleCriterion("TC07", "Bộ vi xử lý (CPU)"),
    SampleCriterion("TC08", "Bộ nhớ RAM"),
    SampleCriterion("TC09", "Ổ cứng SSD"),
    SampleCriterion("TC10", "Màn hình"),
    SampleCriterion("TC11", "Card đồ họa"),
    SampleCriterion("TC12", "Hệ điều hành"),
    SampleCriterion("TC13", "Bản quyền hệ điều hành"),
    SampleCriterion("TC14", "Cổng kết nối"),
    SampleCriterion("TC15", "Bàn phím và chuột"),
    SampleCriterion("TC16", "Nguồn điện"),
    SampleCriterion("TC17", "Nhãn năng lượng"),
    SampleCriterion("TC18", "Kích thước và trọng lượng"),
    SampleCriterion("TC19", "Bảo hành"),
    SampleCriterion("TC20", "Tài liệu hướng dẫn"),
    SampleCriterion("TC21", "Phụ kiện đi kèm"),
)
