# Kế hoạch: E6 AI Auditor (kiểm chữ ký và dấu, rà soát lỗi pháp lý)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E6: L, phase 4, phụ thuộc E4, E5; LLM là Google Gemini qua `google-genai`, không gửi CCCD/PII); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 3 mục 4 (dòng 146–149), DDL `drive_files` (cột `extracted_text`, `has_signature_or_stamp`, `ai_audit_summary`), §8 Phase 4; `CLAUDE.md` (bảo mật khi xử lý file và API ngoài, không để LLM ra quyết định cuối).
**Độ phức tạp:** Lớn (xử lý ảnh/PDF, LLM có cấu trúc đầu ra, kiểm thử bằng bộ mẫu thật).
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e06-ai-auditor`, tạo từ `main` sau khi E5 được merge.
**Phương pháp:** TDD cho phần quy tắc và xác thực đầu ra. Gọi LLM được bọc sau Protocol, test dùng bản giả. Đánh giá chất lượng AI bằng bộ mẫu có nhãn. Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E6 hoàn thành"

| Nhóm | Nội dung | Thuộc E6? |
|---|---|---|
| Chuẩn bị đầu vào: lấy trang cuối của PDF, render thành ảnh, giới hạn kích thước | `app/integrations/document_pages.py` | ✅ Có |
| Cổng LLM (Protocol) và adapter Gemini qua `google-genai` | `app/integrations/llm.py` | ✅ Có |
| Lọc PII trước khi gửi: loại CCCD, số tài khoản, và không gửi file không cần thiết | `app/core/pii_guard.py` (thuần) | ✅ Có |
| Đầu ra có cấu trúc, xác thực bằng Pydantic, coi là dữ liệu không tin cậy | `app/schemas/ai_audit.py` | ✅ Có |
| Kiểm chữ ký và con dấu đỏ trên trang cuối → `has_signature_or_stamp` | `app/services/ai_auditor.py` | ✅ Có |
| Quy tắc xác định (không dùng LLM): thiếu số văn bản, sai tên gói thầu, ngày ủy quyền hết hạn trước ngày ký, thiếu điều khoản | `app/core/legal_audit_rules.py` (thuần) | ✅ Có |
| Ghi kết quả vào `drive_files.ai_audit_summary` và `extracted_text` | `app/services/ai_auditor.py` | ✅ Có |
| Huy hiệu "Đã nhận diện chữ ký" và "Cảnh báo" trên giao diện | `apps/web` | ⏸ Làm sau API |
| AI tự đổi trạng thái hồ sơ sang `VERIFIED_CLOSED` | — | ❌ Không làm (xem mục 5) |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E6 được đánh ✅ khi:** kết quả trên bộ mẫu có nhãn đạt ngưỡng đã chốt ở Q3; không có CCCD trong bất kỳ payload gửi đi (có test); đầu ra LLM sai schema bị từ chối và không ghi vào DB; AI không bao giờ đổi `maturity_status`; mọi lần gọi LLM có giới hạn số lần và ghi chi phí ước tính; coverage ≥ 80%; ruff sạch; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E4 và E5 | ⬜ | Chưa có |
| Cột `extracted_text`, `has_signature_or_stamp`, `ai_audit_summary` | ⬜ | Sẽ có trong `drive_files` (E5) |
| `google-genai` | ⬜ | Chưa có trong `pyproject.toml` |
| Khóa API Gemini | ⬜ | Chưa có. Nạp qua biến môi trường, không commit |
| Xử lý PDF và ảnh | ⬜ | Chưa có thư viện. Chọn ở Q2 |
| Mẫu tích hợp bên ngoài | ⬜ | Dùng cùng mẫu cổng với E5 |
| Bộ mẫu PDF có chữ ký thật | ⬜ | Không có trong repo |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Spec yêu cầu AI "kiểm tra chữ ký/dấu đỏ" nhưng không có bộ mẫu để đo độ chính xác | Hỏi Q1: người dùng cung cấp bộ mẫu có nhãn (đạt và không đạt) |
| S2 | CAO | Phần "sai ngày ủy quyền bảo lãnh hết hạn" cần dữ liệu bảo lãnh từ E7, chưa có ở E4–E5 | Phụ thuộc E7. Nếu E6 làm trước E7, bỏ luật này và thêm sau |
| S3 | TB | Spec yêu cầu không gửi PII sang LLM (CLAUDE.md) nhưng văn bản có thể chứa CCCD trong phụ lục nhân sự | PII guard bắt buộc trước khi gửi (xem Q4) |
| S4 | TB | Văn bản đưa vào LLM có thể chứa câu lệnh ẩn (prompt injection) | Coi nội dung là dữ liệu, không là lệnh. Đầu ra chỉ theo schema, không thực thi gì |
| S5 | THẤP | Spec ghi "Vision/OCR trên trang cuối" nhưng không chọn công cụ | Chọn ở Q2 |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| Gemini API | Chi phí, giới hạn tốc độ, độ trễ | Cần hàng đợi (ARQ, E5) và giới hạn số lần |
| E5 | `drive_files` có file đã đồng bộ | Không có file thì không có đầu vào |
| E7 | Dữ liệu bảo lãnh | Luật ủy quyền hết hạn chờ E7 |
| Bộ mẫu PDF | Có nhãn | Không có thì không đo được chất lượng |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | AI chỉ đề xuất. Người dùng PM xác nhận mới đổi trạng thái hồ sơ | Nếu PM muốn tự động, phải có quyết định mới và ghi rõ rủi ro pháp lý |
| G2 | Ưu tiên quy tắc xác định, chỉ dùng LLM cho chữ ký và các điểm cần đọc hiểu | Thêm luật xác định khi có mẫu lỗi lặp lại |
| G3 | Kết quả được cache theo hash nội dung file, không chạy lại khi file không đổi | Đổi khóa cache nếu cần |
| G4 | Chỉ xử lý trang cuối cho chữ ký, và toàn văn bản cho lỗi pháp lý, khi cần | Đổi phạm vi trang theo mẫu |
| G5 | Mô hình là Gemini đã chốt trong plan epic. Ghi rõ phiên bản cụ thể khi thêm | Đổi model qua cấu hình |

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Bộ mẫu có nhãn để đo chất lượng gồm bao nhiêu file, và ngưỡng chấp nhận là gì? | Tối thiểu 20 file, cân bằng đạt và không đạt. Ngưỡng ví dụ: sai số dưới 10% trên bộ mẫu | ⏸ Chờ người dùng |
| Q2 | Công cụ render PDF và OCR là gì? | Render bằng thư viện nhẹ giấy phép permissive (ví dụ `pypdfium2`). Đọc chữ bằng Gemini, không cài OCR nặng | ⏸ Chờ xác nhận |
| Q3 | Ngưỡng nào đủ để coi là "đã nhận diện chữ ký"? | Đo trên bộ mẫu ở Q1, chốt sau khi có số liệu | ⏸ Chờ dữ liệu |
| Q4 | PII guard có chặn cả trang có nhiều thông tin nhân sự không? | Có. Nếu trang chứa CCCD, chỉ gửi trang cần thiết và che số CCCD bằng mặt nạ trước khi gửi | ⏸ Chờ xác nhận |
| Q5 | Ngân sách gọi LLM mỗi tháng là bao nhiêu? | Đặt hạn mức trong cấu hình, mặc định chặn khi vượt | ⏸ Chờ người dùng |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e06-ai-auditor` từ `main` | ⬜ | |
| 0.2 | Thêm `google-genai` và thư viện render, ghim phiên bản | ⬜ | Chọn theo Q2 |
| 0.3 | Baseline test, coverage, ruff | ⬜ | |

### Pha 1: Quy tắc thuần (unit, không mạng)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ PII guard: CCCD 12 số bị che, số tài khoản bị che, văn bản không PII đi qua nguyên | ⬜ | |
| 1.2 | `app/core/pii_guard.py` | ⬜ | |
| 1.3 | Test đỏ luật pháp lý xác định: thiếu số văn bản, sai tên gói thầu, ủy quyền hết hạn trước ngày ký | ⬜ | Luật ủy quyền chờ E7 (S2) |
| 1.4 | `app/core/legal_audit_rules.py` | ⬜ | |

### Pha 2: Đầu ra có cấu trúc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ: JSON sai schema bị từ chối, JSON hợp lệ được chấp nhận | ⬜ | |
| 2.2 | `app/schemas/ai_audit.py` (Pydantic, `extra="forbid"`) | ⬜ | Mẫu `RequestModel` |

### Pha 3: Adapter và dịch vụ
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Protocol `LLMGateway` và bản giả trong `tests/fakes/` | ⬜ | |
| 3.2 | Adapter Gemini trong `app/integrations/llm.py`, không có test mạng | ⬜ | Chỉ kiểm tra ánh xạ lỗi và timeout |
| 3.3 | `app/services/ai_auditor.py`: kiểm tra cache theo hash, gọi cổng, ghi kết quả | ⬜ | Không commit trong service |
| 3.4 | Test đỏ: AI không đổi `maturity_status` (kiểm tra sau khi chạy) | ⬜ | Quan trọng nhất của epic |

### Pha 4: Job và API
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Job ARQ `audit_drive_file` có giới hạn lượt thử | ⬜ | |
| 4.2 | API: `POST /drive-files/{id}/audit` (PM, rate limit, audit), `GET` kết quả | ⬜ | |

### Pha 5: Đánh giá trên bộ mẫu
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Chạy trên bộ mẫu Q1, ghi số liệu vào plan | ⏸ | Chờ Q1 |
| 5.2 | Chốt ngưỡng ở Q3 | ⏸ | Chờ 5.1 |

### Pha 6: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | Ruff, pytest --cov ≥ 80%, `alembic check` | ⬜ | |
| 6.2 | Kiểm tra bảo mật: PII guard có test, không log nội dung file, khóa API không nằm trong diff | ⬜ | Mục bảo mật bắt buộc |
| 6.3 | Cập nhật `pmis-epics.plan.md` và file plan này | ⬜ | |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E6 | Pha |
|---|---|---|---|
| Kiểm chữ ký và dấu | ⬜ | ✅ (đạt ngưỡng Q3) | 3, 5 |
| Rà soát lỗi pháp lý xác định | ⬜ | ✅ | 1 |
| Không gửi PII | ⬜ | ✅ | 1 |
| AI không tự đóng hồ sơ | ⬜ | ✅ | 3 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Gửi CCCD sang LLM | PII guard có test, chặn trước khi gọi cổng, kiểm tra trong test tích hợp |
| CAO | AI báo "đã có chữ ký" sai, PM tin và đóng hồ sơ | G1: người dùng xác nhận. Đo độ chính xác trên bộ mẫu (Q1) |
| TB | Prompt injection từ nội dung văn bản | Đầu ra theo schema, không thực thi, không đổi trạng thái |
| TB | Chi phí LLM vượt dự kiến | Cache theo hash, hạn mức (Q5) |
| TB | Chất lượng render PDF kém làm mất dấu đỏ | Render độ phân giải đủ cao, kiểm tra trên bộ mẫu |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 3 mục 4. Chưa viết mã. Chờ Q1–Q5 |

## Acceptance

- [x] Plan đã ghi ra file
- [ ] Q1–Q5 đã được chốt
- [ ] Đo chất lượng trên bộ mẫu và ghi số liệu vào plan
- [ ] E6 đạt đủ điều kiện "E6 hoàn thành" ở mục 1
