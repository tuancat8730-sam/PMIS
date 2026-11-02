# Kế hoạch: E11 Auto-Report Studio (báo cáo tuần, meeting note, AI bóc tách biên bản họp)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E11: L, phase 4, phụ thuộc E3, E4, E9; lát cắt cấp tốc đặt E11 sau E9); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 8 (dòng 206–216), Màn hình 5.6 (dòng 547–552), §8 Phase 4 (`docx_generator.py`, AI Auditor, bóc tách biên bản); `CLAUDE.md` (không gửi PII sang LLM, ARQ cho xuất hàng loạt, audit).
**Độ phức tạp:** Lớn. Có hai phần độc lập: phần báo cáo (không AI) và phần AI bóc tách biên bản.
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e11-reports`, tạo từ `main` sau khi E3, E4, E9 được merge.
**Phương pháp:** TDD cho phần tổng hợp dữ liệu và mẫu. Phần AI làm sau cùng, theo cổng LLM đã chốt ở E6. Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E11 hoàn thành"

| Nhóm | Nội dung | Thuộc E11? |
|---|---|---|
| Kỳ báo cáo (tuần, từ thứ Hai đến Chủ nhật), chọn dự án và kỳ | `app/core/report_periods.py` (thuần) | ✅ Có |
| Tổng hợp số liệu tuần: số trường khảo sát và giao hàng, hồ sơ pháp lý, tiến độ mốc, serial, vướng mắc, kiến nghị | `app/services/weekly_report_data.py` | ✅ Có |
| Ba mẫu: báo cáo QLDA tuần, báo cáo giám sát tuần, meeting note giao ban | `app/services/report_templates.py` | ✅ Có (chờ mẫu, Q1) |
| Xuất `.docx` theo thể thức (Nghị định 30/2020, theo spec) | `app/services/docx_generator.py` | ✅ Có (chờ Q2) |
| Bảng `weekly_reports` lưu bản đã xuất và số liệu chốt | Bảng theo ERD (DDL thiếu, Q3) | ✅ Có |
| Kiến nghị phân loại theo đối tượng (Nhà thầu, CĐT, Đơn vị thụ hưởng, TVGS, TVQLDA) | Trường phân loại trên `risk_issues` (E3) | ✅ Có |
| Lưu bản xuất lên Drive | E5 | ⏸ Chờ E5, tạm lưu cục bộ |
| AI bóc tách biên bản họp từ ghi âm `.m4a`/`.mp3` hoặc văn bản `.txt`; ra biên bản dự thảo và danh sách việc cần làm | `app/services/meeting_ai.py` | ✅ Có (Pha cuối) |
| Giao diện Auto-Report Studio | `apps/web` | ⏸ Sau khi API ổn định |
| Trợ lý AI trả lời câu hỏi điều hành (AI PM Copilot) | — | ⏸ Ngoài phạm vi, chưa có trong spec chi tiết |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E11 được đánh ✅ khi:**
- Số liệu tuần khớp với dữ liệu nguồn trên bộ dữ liệu thử (có test so sánh từng con số).
- Xuất đúng ba mẫu, file mở được bằng Word, thể thức khớp mẫu đã chốt (Q2).
- Xuất hai lần cùng kỳ không tạo bản trùng, bản đã xuất được đánh số.
- Phần AI: không có CCCD trong payload (có test); đầu ra sai schema bị từ chối; biên bản dự thảo luôn ở trạng thái "chờ người dùng duyệt".
- Coverage ≥ 80%; ruff sạch; OpenAPI cập nhật; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E3 (mốc, rủi ro, CR/NCR) | 🟡 (đang làm, đã merge PR #4) | `app/models/milestone.py`, `app/models/risk_issue.py`, `app/api/v1/milestones.py`, `app/api/v1/risk_issues.py` |
| Phụ thuộc E4 (hồ sơ pháp lý) | ⬜ | Chưa có |
| Phụ thuộc E9 (serial, giao hàng) | ⬜ | Chưa có |
| Bảng `weekly_reports` | ⬜ | Chưa có |
| Thư viện Word | ⬜ | Chưa có `python-docx` (thêm ở E9) |
| File mẫu báo cáo | ⬜ | Không có trong repo. Spec nhắc mẫu của An Lập Thịnh và Crystal |
| Mẫu dịch vụ đọc | ✅ | `app/services/personnel.py` (E1) |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Lát cắt cấp tốc đặt E11 ngay sau E9, nhưng E11 phụ thuộc E4 mà E4 chưa làm. Báo cáo tuần cần số liệu hồ sơ pháp lý | Làm phần báo cáo không có hồ sơ trước, hoặc đưa E4 lên trước E11 (Q4) |
| S2 | CAO | Không có file mẫu báo cáo tuần và meeting note trong repo | Q1 |
| S3 | CAO | Spec ghi "Nghị định 30/2020" là thể thức nhưng không mô tả các quy tắc cụ thể (cỡ chữ, lề, quốc hiệu, số trang) | Q2 |
| S4 | TB | Spec không có DDL `WEEKLY_REPORTS`, chỉ có trong ERD | Đề xuất cấu trúc ở mục 5, chờ Q3 |
| S5 | TB | "Đối với Nhà thầu / CĐT / …" cần phân loại kiến nghị, nhưng `risk_issues` (E3) chưa có trường này | Thêm cột phân loại đối tượng, migration của E11 |
| S6 | TB | Spec yêu cầu AI "bóc tách biên bản họp từ file ghi âm `.m4a`" nhưng chưa rõ dùng Gemini nhận âm thanh hay công cụ chuyển giọng nói thành chữ trước | Q5 |
| S7 | THẤP | File "họp triển khai 21.10.txt" là ví dụ đầu vào. Không có trong repo | Cần file mẫu để kiểm thử (Q1) |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E3 | Mốc, rủi ro, CR/NCR | Hiện đang làm, đã có API |
| E4 | Trạng thái hồ sơ pháp lý | Chưa có. Thiếu thì mục "tình trạng hồ sơ" trống |
| E9 | Số liệu khảo sát, giao hàng, serial | Chưa có. Thiếu thì mục giao hàng trống |
| E5 | Lưu lên Drive | Có thể làm sau |
| Gemini | Phần AI | Dùng lại cổng LLM của E6 nếu E6 xong trước; nếu không, làm cổng riêng |
| Mẫu và thể thức | Không có trong repo | Không kiểm thể thức được |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Kỳ báo cáo là tuần theo lịch Thứ Hai đến Chủ nhật (khớp "Tuần 03: 26/10–01/11/2026" của spec) | Đổi trong `report_periods.py` |
| G2 | Số liệu tuần được chốt khi xuất. Bản đã xuất lưu lại số liệu đã dùng, không tính lại | Nếu cần tính lại, thêm bản xuất mới |
| G3 | Trường phân loại kiến nghị là khóa cố định trong code (5 đối tượng) | Chuyển thành bảng nếu PM muốn thêm đối tượng |
| G4 | Biên bản họp do AI sinh là bản nháp, không có chữ ký | Theo nguyên tắc người dùng duyệt |

Cấu trúc đề xuất `weekly_reports` (chờ Q3): `project_id`, `period_start`, `period_end`, `kind` (`PM_WEEKLY`, `SUPERVISION_WEEKLY`, `MEETING_NOTE`), `version` (số thứ tự xuất), `data_snapshot` (JSONB số liệu đã chốt), `docx_local_path`, `created_by`, `created_at`. Unique theo `(project_id, kind, period_start, version)`.

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Có các file mẫu báo cáo tuần, giám sát tuần, meeting note và file ghi âm/văn bản họp mẫu không? | Người dùng cung cấp, đã ẩn dữ liệu nhạy cảm | 🟡 Người dùng chọn "tạo file mẫu trước": đã tạo bản nháp tự làm tại `docs/report-samples/e11-sample-templates.md`. Mẫu thật và file ghi âm vẫn chờ |
| Q2 | Quy tắc thể thức chi tiết là gì (font, cỡ chữ, lề, quốc hiệu, tiêu ngữ, số trang)? | Lấy trực tiếp từ file mẫu bằng cách đọc cấu hình style của mẫu, không tự đoán | ⏸ Chờ người dùng |
| Q3 | Cấu trúc `weekly_reports` là gì? | Dùng cấu trúc mục 5 | ⏸ Chờ xác nhận |
| Q4 | Thứ tự với E4 ra sao? | Đề xuất đưa E4 lên trước E11. Nếu gấp, làm phần báo cáo không có hồ sơ và ghi rõ mục đó "chưa đủ dữ liệu" | ⏸ Chờ người dùng |
| Q5 | Chuyển giọng nói thành chữ bằng gì? | Gemini nhận âm thanh trực tiếp, giảm số bước. Không gửi PII. Kiểm chất lượng trên file mẫu | ⏸ Chờ xác nhận |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e11-reports` từ `main` | ⏸ | Chưa tạo, làm trên nhánh hiện tại (`feat/e10-field-pwa`) |
| 0.2 | Baseline test, coverage, ruff, alembic head | ⬜ | |

### Pha 1: Kỳ báo cáo và tổng hợp số liệu
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: kỳ báo cáo từ Thứ Hai đến Chủ nhật; kỳ tuần 03 là 26/10–01/11/2026 (theo spec) | ✅ | `tests/unit/test_report_periods.py` (5 test) |
| 1.2 | `app/core/report_periods.py` | ✅ | `week_period_containing(day)` |
| 1.3 | Test đỏ: số liệu tuần khớp dữ liệu nguồn trên bộ dữ liệu thử | ⬜ | |
| 1.4 | `app/services/weekly_report_data.py` | ⬜ | Không N+1 |

### Pha 2: Mẫu và xuất .docx
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Chờ mẫu (Q1, Q2). Không bắt đầu trước | 🟡 | Đã tạo bản nháp `docs/report-samples/e11-sample-templates.md` (ba mẫu, ánh xạ placeholder tới bảng). Chờ mẫu thật để đối chiếu thể thức |
| 2.2 | Test đỏ: xuất hai lần cùng kỳ tạo bản đánh số tăng dần, không ghi đè | ⬜ | |
| 2.3 | `app/services/docx_generator.py` và `report_templates.py` | 🟡 | `render_report_docx` và ba mẫu đã có, có test. Chưa trộn dữ liệu thật vào mẫu (cần bảng snapshot). `python-docx==1.1.2` đã thêm vào `pyproject.toml` |
| 2.4 | Test so sánh cấu trúc file xuất với mẫu | ⬜ | |
| 2.5 | Model `WeeklyReport`, migration, API xuất và tải về, rate limit, audit | ⬜ | |

### Pha 3: Phân loại kiến nghị
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ: kiến nghị có đối tượng, lọc theo đối tượng | ⬜ | |
| 3.2 | Thêm cột phân loại vào `risk_issues` (migration) | ⬜ | Thay đổi nhỏ ở E3, có test hồi quy |

### Pha 4: AI bóc tách biên bản họp (sau E6 hoặc có cổng riêng)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ PII guard cho transcript: không để lộ CCCD | ⬜ | Dùng `app/core/pii_guard.py` của E6 nếu có |
| 4.2 | Test đỏ: đầu ra sai schema bị từ chối; biên bản dự thảo có trạng thái `DRAFT` | ⬜ | |
| 4.3 | Job ARQ bóc tách: kết quả là biên bản `.docx` dự thảo và danh sách việc cần làm có người phụ trách và hạn | ⬜ | |
| 4.4 | Chất lượng trên file mẫu, ghi số liệu vào plan | ⏸ | Chờ Q1 |

### Pha 5: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Ruff, pytest --cov ≥ 80%, `alembic check` | ⬜ | |
| 5.2 | Kiểm bảo mật: file tải lên có giới hạn, PII không vào LLM, không log nội dung | ⬜ | |
| 5.3 | Cập nhật `pmis-epics.plan.md` và file plan này | ⬜ | |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E11 | Pha |
|---|---|---|---|
| Kỳ báo cáo và số liệu tuần | ⬜ | ✅ | 1 |
| Ba mẫu .docx | ⬜ | ✅ (chờ Q1, Q2) | 2 |
| Phân loại kiến nghị | ⬜ | ✅ | 3 |
| AI bóc tách biên bản | ⬜ | ✅ (Pha cuối) | 4 |
| Lưu lên Drive | ⬜ | ⏸ | Sau E5 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Thiếu mẫu, không kiểm được thể thức | Q1, Q2. Pha 2 bị chặn, các pha khác vẫn chạy |
| CAO | E4 và E9 chưa xong khi cần báo cáo đầu tiên | Q4: đề xuất đưa E4 lên trước |
| CAO | AI gửi thông tin nhân sự trong transcript sang LLM | Pha 4 có PII guard và test trước khi gọi |
| TB | Số liệu tuần lệch giữa các mục | Test so sánh từng con số, bản xuất lưu snapshot |
| TB | Chất lượng nhận dạng giọng nói tiếng Việt | Kiểm trên file mẫu, có thể sửa tay trước khi duyệt |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 8 và Màn hình 5.6. Phát hiện S1–S7. Chưa viết mã |
| 2026-11-01 | Pha 1 một phần: kỳ báo cáo (1.1, 1.2) xong theo TDD, 5 test xanh. Chưa làm 1.3, 1.4 (số liệu tuần cần dữ liệu thử và DB để kiểm). Chưa tạo nhánh `feat/e11-reports`: làm trên `feat/e10-field-pwa` hiện tại. Pha 2 bị chặn bởi Q1, Q2 (không có mẫu, không có quy tắc thể thức). Pha 3, 4 chưa làm. Plan `pmis-epics` ghi E4, E9 là "chưa làm" nhưng git log cho thấy E9 đã merge: cần đối chiếu lại trước khi chạy 1.4 |
| 2026-11-01 | Tạo bản nháp mẫu báo cáo (ba mẫu, placeholder ánh xạ tới bảng) tại `docs/report-samples/e11-sample-templates.md`. Chưa xuất `.docx` vì `python-docx` chưa được cài, và chưa khai báo trong `pyproject.toml`. Cần quyết định riêng để thêm dependency. Thể thức Nghị định 30/2020 chưa đối chiếu |
| 2026-11-01 | Người dùng đồng ý thêm `python-docx`. Pha 2 một phần: `render_report_docx` và `report_templates` có test (6 test xanh). Chưa làm: endpoint xuất, bảng `weekly_reports`, migration, đánh số bản, audit. Đang chờ người dùng gửi đường dẫn file mẫu thật để đối chiếu thể thức |

## Acceptance

- [x] Plan đã ghi ra file
- [ ] Q1–Q5 đã được chốt
- [ ] Số liệu tuần khớp dữ liệu nguồn
- [ ] Ba mẫu xuất đúng thể thức
- [ ] E11 đạt đủ điều kiện "E11 hoàn thành" ở mục 1
