# Kế hoạch: E4 Checklist pháp lý 89+ hồ sơ và máy trạng thái trưởng thành

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E4: M, phase 2, phụ thuộc E1); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 3 mục 1–2 (dòng 131–150), DDL `doc_maturity_status` và `legal_documents` (dòng 388–428), §7 (seed hồ sơ pháp lý), §8 Phase 2; `CLAUDE.md` (dữ liệu khóa, audit cùng transaction, service không commit, TDD).
**Độ phức tạp:** Trung bình (1 bảng chính, 1 enum, máy trạng thái, seed phụ thuộc dữ liệu chưa có).
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e04-legal`, tạo từ `main` sau khi E3 được merge.
**Phương pháp:** rà soát tĩnh `apps/api` và đối chiếu spec. TDD: test đỏ → xanh → refactor. Q1–Q4 đã chốt ngày 2026-10-31 (mục 6). Chưa viết mã.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E4 hoàn thành"

| Nhóm | Nội dung | Thuộc E4? |
|---|---|---|
| Enum `doc_maturity_status` (7 giá trị theo DDL spec) | `app/models/legal_document.py`, migration mới | ✅ Có |
| Bảng `legal_documents` theo DDL spec, trừ 2 cột FK tới `drive_files` (thêm ở E5) | `app/models/legal_document.py` | ✅ Có |
| Máy trạng thái trưởng thành: hàm thuần kiểm tra chuyển trạng thái hợp lệ | `app/core/legal_maturity_rules.py` (không DB) | ✅ Có |
| Đổi trạng thái ghi audit cùng transaction; `VERIFIED_CLOSED` chỉ PM đóng được | `app/services/legal_documents.py`, router | ✅ Có |
| API liệt kê (lọc theo `phase_group`, `maturity_status`), xem chi tiết, tạo, sửa, đổi trạng thái | `app/api/v1/legal_documents.py` | ✅ Có |
| API tổng hợp đếm theo trạng thái và giai đoạn (phục vụ E12 và panel trái màn hình 5.2) | `app/services/legal_documents.py` | ✅ Có |
| Seed checklist 89+ đầu mục và bảng tình trạng hồ sơ thực tế của 2 dự án (từ file Excel PM cung cấp) | `app/db/seed_real_projects.py` (mở rộng), file dữ liệu | ⏸ Chờ file Excel (Q1 đã chốt) |
| Liên kết file Drive (`draft_drive_file_id`, `signed_drive_file_id`) | E5 | ⏸ Thuộc E5 |
| Đánh dấu "Có lỗi pháp lý" tự động bằng AI | E6 | ⏸ Thuộc E6 |
| Giao diện Legal & Drive Hub (màn hình 5.2) | `apps/web` | ⏸ Làm sau khi API ổn định |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E4 được đánh ✅ khi:** migration round-trip sạch, `alembic check` không drift; mọi chuyển trạng thái hợp lệ và không hợp lệ có unit test; API có test tích hợp (200, 403, 404, 409, 422, audit, 429 ở endpoint ghi); hồ sơ `VERIFIED_CLOSED` không sửa được trực tiếp; seed idempotent khi đã có dữ liệu; coverage ≥ 80%; ruff sạch; OpenAPI cập nhật; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E1 (dự án, quyền theo dự án) | ✅ | `apps/api/app/api/deps.py:106` `project_role_guard`; `ANY_PROJECT_ROLE` ở dòng 23 |
| Bảng `legal_documents` | ⬜ | Chưa có model |
| Enum `doc_maturity_status` | ⬜ | Chưa có |
| Danh mục 89+ đầu mục | ⬜ | Spec chỉ nêu 5 giai đoạn và ví dụ, không liệt kê đủ 89 đầu mục trong repo |
| Mẫu model | ✅ | `app/models/contract.py:1-30`: `Mapped`, `mapped_column`, `text("gen_random_uuid()")` |
| Mẫu enum lưu UPPER_SNAKE | ✅ | `app/models/project.py:12-16`: `StrEnum` + `enum_values` |
| Mẫu quy tắc thuần | ✅ | `app/core/schedule_rules.py`, `app/core/record_codes.py`; unit test `tests/unit/test_schedule_rules.py` |
| Mẫu service không commit | ✅ | `app/services/contracts.py:8-18`: chỉ `session.add` và `flush` |
| Mẫu router ghi | ✅ | `app/api/v1/contracts.py:15-35`: `project_role_guard(Role.PM)`, `WriteRateLimitDep`, `record_audit`, `session.commit()` |
| Mẫu test tích hợp | ✅ | `tests/integration/test_contracts_api.py:1-40`: `pytestmark`, AAA, `login_as`, `create_project` |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Spec yêu cầu checklist 89+ đầu mục nhưng không liệt kê đủ trong tài liệu. Không có nguồn để seed | Đã chốt Q1: PM cung cấp file Excel. Chờ file |
| S2 | CAO | Spec §7 yêu cầu nạp "bảng tình trạng hồ sơ pháp lý thực tế" của 2 dự án, nhưng không có dữ liệu trong repo | Gộp vào Q1 (file Excel PM cung cấp) |
| S3 | TB | `legal_documents.draft_drive_file_id` và `signed_drive_file_id` tham chiếu `drive_files`, bảng thuộc E5 | Đã chốt Q2: E4 tạo bảng không FK, E5 thêm FK bằng migration riêng |
| S4 | TB | Trạng thái `VERIFIED_CLOSED` là "PM đã kiểm tra pháp lý & đóng checklist", nhưng spec không nói ai được mở lại | Đã chốt Q3: PM hoặc ADMIN, bắt buộc lý do và audit |
| S5 | THẤP | `phase_group` là VARCHAR tự do trong DDL, còn spec liệt kê 5 giai đoạn | Dùng enum 5 giá trị, lưu UPPER_SNAKE (CLAUDE.md) |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E1 | `projects`, `project_members` | Chặn nếu thiếu. Đã có |
| Dữ liệu PM | Danh mục 89 đầu mục, số hiệu văn bản, hạn đôn đốc | Không seed được nếu thiếu. API vẫn chạy được với dữ liệu nhập tay |
| Nội dung pháp lý | Căn cứ NĐ 45/2026, 224/2026 | PM domain xác nhận checklist trước khi seed (rủi ro đã ghi trong `pmis-epics.plan.md`) |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Một dòng `legal_documents` thuộc một dự án và một giai đoạn | Nếu một văn bản dùng chung cho nhiều dự án, cần bảng liên kết |
| G2 | Trạng thái lưu cứng trên dòng, không tính từ ngày | Khớp với S3 của E3: trạng thái do người dùng chọn, không suy ra |
| G3 | Chỉ ghi mới qua API, không có import Excel ở E4 | Thêm import ở E4 nếu PM có sẵn Excel checklist |
| G4 | `stt` duy nhất trong một dự án | Nếu spec đổi cách đánh số, đổi ràng buộc unique |

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Nguồn danh mục 89+ đầu mục và bảng tình trạng hồ sơ thực tế là gì? | File Excel do PM cung cấp, nạp qua script seed idempotent | ✅ Đã chốt: file Excel do PM cung cấp. Chờ file |
| Q2 | Có tách E5 để thêm FK `drive_file_id` không? | Tách như mục S3 | ✅ Đã chốt: có, tách. E5 thêm FK |
| Q3 | Sau `VERIFIED_CLOSED`, ai được mở lại và cách mở? | PM hoặc ADMIN. Ghi lý do và audit. Mở lại chuyển về `SIGNED_SCAN_PDF` | ✅ Đã chốt: PM hoặc ADMIN, bắt buộc lý do và audit |
| Q4 | Có cho phép đi lùi trạng thái (ví dụ `SUBMITTED_REVIEW` về `DRAFT_DOCX`) không? | Có, nhưng bắt buộc có lý do và ghi audit | ✅ Đã chốt: có, bắt buộc lý do và audit |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Tạo nhánh `feat/e04-legal` từ `main` | ✅ | Tạo từ `main` (91a09d9) |
| 0.2 | Baseline: pytest integration, coverage, ruff, alembic head | ✅ | Pytest 183 pass, 1 skip; coverage 86,71%; ruff sạch; alembic head `e8b2c5f1a3d4`. Chạy trên PostgreSQL container cổng 5433 (`pmis_test`) |

### Pha 1: Máy trạng thái (unit, không DB)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ `tests/unit/test_legal_maturity_rules.py`: chuyển hợp lệ, không hợp lệ, `VERIFIED_CLOSED` là trạng thái khóa | ✅ | Đỏ: lỗi import khi chưa có module |
| 1.2 | `app/core/legal_maturity_rules.py`: bảng chuyển trạng thái, hàm `can_transition` | ✅ | Xanh: 19 test. Thêm `is_locked`, `requires_reason` |

### Pha 2: Model và migration
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Model `LegalDocument` và enum `DocMaturityStatus`, `LegalPhaseGroup` | ✅ | Mẫu `app/models/contract.py` |
| 2.2 | Migration có `downgrade` xóa enum (mẫu `6b19966287e0`) | ✅ | Migration `f3a9c1d07b2e`; round-trip và `alembic check` sạch |

### Pha 3: Service và router
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ IT: tạo, lọc, đổi trạng thái hợp lệ, đổi trạng thái sai (409), `VERIFIED_CLOSED` bị khóa (409), 403, 404, 429 | ✅ | Đỏ: 16 test lỗi trước khi có API |
| 3.2 | `app/services/legal_documents.py` (không commit) | ✅ | Mẫu `app/services/contracts.py` |
| 3.3 | `app/api/v1/legal_documents.py`, audit cùng transaction, rate limit ở endpoint ghi | ✅ | Mẫu `app/api/v1/contracts.py`. Đã đăng ký trong `app/api/v1/__init__.py` |
| 3.4 | API tổng hợp đếm theo trạng thái và giai đoạn | ✅ | `GROUP BY` một truy vấn, ô trống điền 0 |

### Pha 4: Seed (sau khi có dữ liệu Q1)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ: seed hai lần cho cùng số dòng | ⏸ | Chưa viết: cần hàm seed và file Excel từ PM (Q1). Ràng buộc unique `(project_id, stt)` đã có ở migration |
| 4.2 | Mở rộng `seed_real_projects.py` | ⏸ | Chờ file Excel từ PM (Q1) |

### Pha 5: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Ruff, pytest --cov ≥ 80%, `alembic check`, round-trip migration | ✅ | Ruff sạch; pytest 219 pass, 1 skip; coverage 86,19%; round-trip và `alembic check` sạch |
| 5.2 | Tự review diff: không secret, không `print`, không `.env` | ✅ | Đã rà các file mới; không secret, không `print` |
| 5.3 | Cập nhật `pmis-epics.plan.md` và file plan này | ✅ | Đã cập nhật cả hai |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E4 | Pha |
|---|---|---|---|
| Máy trạng thái 7 trạng thái | ✅ | ✅ | 1 |
| Bảng và API hồ sơ | ✅ | ✅ | 2, 3 |
| Khóa `VERIFIED_CLOSED` | ✅ | ✅ | 3 |
| Seed 89+ đầu mục | ⬜ | ⏸ | 4 (chờ Q1) |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Danh mục 89 đầu mục không đủ hoặc sai nội dung pháp lý | Q1: PM xác nhận trước khi seed. Không hard-code danh mục trong code |
| TB | Trạng thái bị đổi sai thứ tự khi nhiều người cùng sửa | Kiểm tra chuyển trạng thái ở service, trả 409 khi trạng thái cũ không khớp |
| TB | Mất dấu vết khi mở lại hồ sơ đã khóa | Q3: bắt buộc lý do và audit |
| THẤP | Enum PostgreSQL khó thay đổi về sau | Dùng `StrEnum` và kiểm tra downgrade như mục 2.2 |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 3 và DDL `legal_documents`. Chưa viết mã |
| 2026-10-31 | Người dùng chốt Q1–Q4 theo đề xuất. Q1 còn chờ file Excel từ PM để làm Pha 4 |
| 2026-10-31 | Pha 0 xong trên nhánh `feat/e04-legal`. Baseline: 183 pass, 1 skip, coverage 86,71%, ruff sạch, alembic head `e8b2c5f1a3d4` |
| 2026-10-31 | Xong Pha 1–3 và 5: máy trạng thái, migration `f3a9c1d07b2e`, API (CRUD, transitions, summary, 429). Chuyển trạng thái đi lùi và mở lại cần lý do, ghi audit. Dời `helpers.limited_client` sang dùng chung. Kết quả: 219 pass, 1 skip, coverage 86,19%. Pha 4 còn chờ file Excel. Chưa commit |

## Acceptance

- [x] Plan đã ghi ra file
- [x] Q1–Q4 đã được chốt
- [ ] File Excel danh mục 89+ đầu mục đã nhận (Pha 4)
- [ ] E4 đạt đủ điều kiện "E4 hoàn thành" ở mục 1
