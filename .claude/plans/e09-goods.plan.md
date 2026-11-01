# Kế hoạch: E9 Module thiết bị (hàng mẫu 21 tiêu chí, serial/IMEI, CO/CQ, ma trận 62×4×3, 240+ biên bản .docx)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E9: XL, phase 3, phụ thuộc E1, E2); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 6 (dòng 181–197), Phân hệ 1 mục 2 (template 2), Màn hình 5.3 (dòng 528–533), DDL `equipment_catalog`, `delivery_handovers`, `equipment_serials` (dòng 430–478), §7 (seed Lâm Đồng), §8 Phase 3–4; `CLAUDE.md` (Idempotency-Key cho lệnh ghi từ thiết bị, dữ liệu khóa, ARQ cho xuất hàng loạt).
**Độ phức tạp:** Rất lớn. Năm nhóm chức năng và một luồng sinh 240+ file. Nên chia thành 4 đợt nhỏ, mỗi đợt có điều kiện ✅ riêng.
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e09-goods`, tạo từ `main` sau khi E2 được merge. Đây là epic trong lát cắt cấp tốc, nên ưu tiên hơn E8.
**Phương pháp:** TDD. Quy tắc viết thuần, test tích hợp trên PostgreSQL 16 thật. Chưa viết mã; chờ người dùng chốt mục 6, đặc biệt là file mẫu biên bản.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E9 hoàn thành"

| Nhóm | Nội dung | Thuộc E9? |
|---|---|---|
| Đợt A: danh mục hàng hóa và kiểm định hàng mẫu 21 tiêu chí (`equipment_catalog`, `sample_inspections`) | `app/models/equipment.py`, `app/core/sample_criteria.py` | ✅ Có |
| Đợt B: kho serial và CO/CQ: import Excel, chống trùng, so sánh thiếu hụt theo đợt, phân bổ về trường | `equipment_serials`, `app/services/serial_registry.py`, `app/core/serial_shortage_rules.py` | ✅ Có |
| Đợt C: ma trận giao hàng 62 đơn vị × 4 cụm × 3 đợt; lịch giao; trạng thái từng trường | `delivery_handovers`, `app/core/delivery_matrix.py` | ✅ Có |
| Đợt D: sinh biên bản `.docx` hàng loạt (240+ file) qua ARQ, đóng gói zip, idempotent | `app/services/handover_docx.py`, `app/worker/` | ✅ Có (cần file mẫu, Q1) |
| Tab "Tổng quan" và màn hình quản trị thiết bị | `apps/web` | ⏸ Sau khi API ổn định |
| Ảnh hiện trường, quét QR tại điểm trường | E10 | ⏸ Thuộc E10 |
| Đẩy file biên bản lên Drive | Khung của E5 | ⏸ Chờ E5 (có thể lưu cục bộ trước) |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E9 được đánh ✅ khi:**
- Migration round-trip sạch, `alembic check` không drift.
- Serial không trùng trong một dự án (ràng buộc unique và có test). Import file có một serial trùng thì từ chối cả file, không nhập một phần.
- Kiểm định 21 tiêu chí: mỗi tiêu chí có kết quả `ĐẠT` hoặc `KHÔNG ĐẠT`; mẫu có một `KHÔNG ĐẠT` thì kết luận `YÊU CẦU LÀM LẠI MẪU`.
- Sinh đủ số biên bản theo ma trận (62 đơn vị × 3 đợt + 62 tổng thể = 248 file, khớp "240+" của spec). Có test so sánh số file và cấu trúc thể thức với file mẫu.
- Chạy lại sinh biên bản không tạo bản trùng.
- Seed Lâm Đồng idempotent và khớp §7.
- Coverage ≥ 80%, ruff sạch, OpenAPI cập nhật, plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E1 và E2 | ✅ | `app/models/beneficiary_unit.py`, `app/api/v1/beneficiary_units.py`, `app/db/seed_real_projects.py` (E2) |
| Quyền theo dự án | ✅ | `app/api/deps.py:106` `project_role_guard` |
| Seed 62 đơn vị Lâm Đồng | 🟡 | Đang chờ dữ liệu B1 (E2). Xem `e02-beneficiary.plan.md` |
| Bảng `equipment_catalog`, `delivery_handovers`, `equipment_serials` | ⬜ | Chưa có |
| `sample_inspections` và `delivery_batch_items` | ⬜ | Chỉ có trong ERD, không có DDL |
| Thư viện Excel | ⬜ | Chưa có `openpyxl` |
| Thư viện Word | ⬜ | Chưa có `python-docx` |
| ARQ | ⬜ | Được thêm ở E5. E9 đợt D phụ thuộc E5 hoặc tự đưa ARQ vào (Q4) |
| File mẫu biên bản bàn giao | ⬜ | Không có trong repo |
| Mẫu import và quy tắc thuần | ✅ | `app/services/personnel.py` (E1), `tests/unit/test_personnel_rules.py` |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Không có file mẫu biên bản bàn giao (`.docx`) trong repo. Không kiểm được thể thức | Hỏi Q1 |
| S2 | CAO | `sample_inspections` và `delivery_batch_items` có trong ERD, không có DDL | Đề xuất cấu trúc ở mục 5, chờ Q2 |
| S3 | CAO | §7 ghi mã `A3520` 1.420 bộ (Đợt 1) và `H4350G` 31 bộ. Chưa rõ 31 bộ `H4350G` thuộc đợt nào và có nằm trong ma trận giao hay không | Hỏi Q3 |
| S4 | TB | Số file 240+ = 62 × 3 + 62 = 248. Cách đếm này suy ra từ spec, chưa có xác nhận | Ghi là giả định, kiểm tra với Q1 |
| S5 | TB | §7 ghi "Đợt 1: Tin học 60 đơn vị" nhưng ma trận có 62 đơn vị. Chênh 2 đơn vị | Hỏi Q3 cùng câu hỏi |
| S6 | THẤP | Serial 320/1.420 đã nộp, thiếu 1.100 (Phân hệ 1 mục 1, dòng 104, và §5.1). Số liệu khớp: 1.420 − 320 = 1.100 | Không cần hỏi, đã khớp |
| S7 | THẤP | Mô tả 21 tiêu chí chỉ có ví dụ (CPU, RAM, SSD, HĐH bản quyền, bảo hành, ISO/RoHS…). Danh sách đủ 21 chưa có | Hỏi Q4 |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E2 | 62 đơn vị và cụm | Chờ B1 (dữ liệu Lâm Đồng). Không có thì không sinh được ma trận |
| E5 | Đẩy file lên Drive và ARQ | Đợt D có thể làm trước bằng lưu cục bộ, nhưng cần ARQ |
| File Excel serial | Nhà thầu gửi, định dạng có thể đổi | Kiểm tra tiêu đề cột, từ chối file sai định dạng |
| Mẫu biên bản | Thể thức hành chính | Thiếu mẫu thì không xác nhận đợt D được |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | `equipment_catalog` là một dòng cho mỗi mã hàng trong một dự án và một đợt | Nếu cùng mã dùng cho nhiều đợt, đổi khóa unique |
| G2 | `sample_inspections` là một dòng cho mỗi lần kiểm, với kết quả 21 tiêu chí trong JSONB có cấu trúc đã validate | Nếu cần truy vấn từng tiêu chí, tách thành bảng con |
| G3 | `delivery_handovers` là một dòng cho mỗi cặp (trường, đợt), tức 62 × 3 = 186 dòng, cộng dòng "tổng thể" cho mỗi trường | Đổi nếu Q3 quy định khác |
| G4 | Serial là khóa duy nhất trong dự án (`UNIQUE(project_id, serial_number_primary)` theo DDL) | Theo DDL, không đổi nếu không có quyết định mới |
| G5 | Biên bản sinh ra là bản nháp `.docx`. Bản đã ký là file quét do người dùng tải lên | Theo DDL `generated_docx_drive_id` và `signed_scan_drive_id` |

Cấu trúc đề xuất cho `sample_inspections` (chờ Q2): `equipment_id`, `inspected_on`, `inspector`, `serial_number_sample`, `criteria_results` (JSONB 21 phần tử: mã tiêu chí, giá trị hợp đồng, giá trị thực tế, kết quả), `conclusion` (`ĐẠT` hoặc `YÊU CẦU LÀM LẠI MẪU`).

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Có file mẫu biên bản bàn giao (`.docx`) và mẫu công văn không? | Người dùng cung cấp file mẫu đã ẩn dữ liệu nhạy cảm. Không có thì đợt D chờ | ⏸ Chờ người dùng |
| Q2 | Cấu trúc `sample_inspections` và `delivery_batch_items` có đúng như mục 5 không? | ✅ Đồng ý mục 5 (2026-11-01) | Chốt |
| Q3 | Đơn vị đếm và số đơn vị đợt 1 là gì (60 hay 62)? Và 31 bộ `H4350G` thuộc đợt nào? | ✅ 62 đơn vị, đơn vị đếm là bộ máy (2026-11-01). Vụ 31 bộ `H4350G` chưa trả lời | Chốt số đơn vị; `H4350G` còn mở |
| Q4 | Danh sách đủ 21 tiêu chí kiểm định là gì? Đưa ARQ vào E9 hay đợi E5? | ✅ ARQ đợi E5, đợt D chạy đồng bộ tạm (2026-11-01). Danh sách 21 tiêu chí: người dùng chưa gửi | Chờ danh sách 21 tiêu chí (chặn A2 hoàn chỉnh) |
| Q5 | Chính sách "chỉ một biên bản đã ký cho mỗi trường và đợt" có đúng không? | ✅ Đúng. Ký lại thay bản cũ qua bản ghi điều chỉnh có audit (2026-11-01) | Chốt |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor. Chia thành 4 đợt, mỗi đợt có điều kiện ✅ riêng để có thể giao từng phần.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e09-goods` từ `main` | ✅ | Tạo ngày 2026-11-01 |
| 0.2 | Thêm `openpyxl` (đợt B) và `python-docx` (đợt D), ghim phiên bản | ⬜ | Chưa cần: đợt B4 (Excel) làm sau |
| 0.3 | Baseline test, coverage, ruff, alembic head | 🟡 | Unit: 157 xanh trước thay đổi. Chưa có `TEST_DATABASE_URL` nên integration và alembic chưa chạy |

### Đợt A: Danh mục và kiểm định hàng mẫu
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| A1 | Test đỏ: 21 tiêu chí, một tiêu chí `KHÔNG ĐẠT` thì kết luận làm lại mẫu | ✅ | `tests/unit/test_sample_criteria.py`, 7 test, đã đỏ rồi xanh |
| A2 | `app/core/sample_criteria.py` (thuần) + `sample_criteria_catalog.py` | 🟡 | Logic xong. Danh mục 21 tiêu chí là TẠM do đội tự soạn theo spec (người dùng yêu cầu); thay bằng phụ lục hợp đồng khi có |
| A3 | Model `EquipmentCatalog`, `SampleInspection`, migration | ✅ | Migration `c5d9a1e7f3b2`: round-trip sạch, `alembic check` không drift (PostgreSQL 16) |
| A4 | Service và router CRUD, audit, rate limit ở endpoint ghi | ✅ | Code xong: `services/equipment.py`, `api/v1/equipment.py`. 5 endpoint. 6 test tích hợp xanh trên PostgreSQL 16 |

### Đợt B: Kho serial và CO/CQ
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| B1 | Test đỏ: import có một serial trùng thì từ chối cả file | 🟡 | Phần thuần `find_duplicate_serials` và `DuplicateSerialError` xong. Chưa nối vào import Excel (B4) |
| B2 | Test đỏ: thiếu hụt = số cần giao − số đã nộp, theo đợt | ✅ | Khớp mẫu 1.420 − 320 = 1.100 |
| B3 | `app/core/serial_shortage_rules.py` | ✅ | Gồm `serial_shortage`, `find_duplicate_serials`, `co_cq_status`. 10 test |
| B4 | Import Excel: kiểm tiêu đề cột, giới hạn kích thước, từ chối file sai định dạng | ⬜ | Mục bảo mật: file người dùng gửi lên |
| B5 | Model `EquipmentSerial` và migration, ràng buộc unique | ✅ | Unique `(project_id, serial_number_primary)`, kiểm trên PostgreSQL 16 |
| B6 | Phân bổ serial về trường, không cho một serial thuộc hai trường | ⬜ | |

### Đợt C: Ma trận giao hàng
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| C1 | Test đỏ: sinh đủ 62 × 3 dòng `delivery_handovers` cộng dòng tổng thể | ✅ | Q3 đã chốt 62. 248 dòng = 62 × (3 + 1) |
| C2 | `app/core/delivery_matrix.py` (thuần) | ✅ | Gồm sinh ô (đơn vị, đợt) và bảng chuyển trạng thái. Bảng chuyển là GIẢ ĐỊNH, chờ người dùng chốt |
| C3 | Model `DeliveryHandover`, migration | ✅ | Unique `(project_id, beneficiary_unit_id, batch_code)`, kiểm trên PostgreSQL 16 |
| C4 | API: lọc theo cụm và đợt, đổi trạng thái theo bảng chuyển đã chốt | ✅ | Code xong: `services/delivery_handovers.py`, `api/v1/delivery_handovers.py`, 4 endpoint (sinh, lọc, đổi trạng thái). Bảng chuyển vẫn là giả định. Quyền đổi trạng thái: PM, TVGS, kỹ sư hiện trường (giả định). 5 test tích hợp xanh trên PostgreSQL 16 |

### Đợt D: Sinh biên bản .docx hàng loạt
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| D1 | Chờ file mẫu (Q1). Không bắt đầu trước | ⏸ | Điều kiện chặn |
| D2 | Test đỏ: sinh hai lần không tạo file trùng; tên file theo quy ước đã chốt | ⬜ | |
| D3 | `app/services/handover_docx.py`: trộn dữ liệu vào mẫu, không ghép chuỗi tay | ⬜ | Thể thức theo file mẫu |
| D4 | Test so sánh cấu trúc với mẫu (số đoạn, bảng, tiêu đề) | ⬜ | So cấu trúc, không so byte |
| D5 | Job sinh hàng loạt chạy theo lô, ghi tiến độ | ⬜ | ARQ theo Q4 |
| D6 | Đóng gói zip theo cụm và đợt | ⬜ | |

### Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| K1 | Ruff, pytest --cov ≥ 80%, `alembic check`, round-trip migration | ⬜ | |
| K2 | Seed Lâm Đồng idempotent và khớp §7 | ⬜ | Chờ dữ liệu B1 của E2 |
| K3 | Cập nhật `pmis-epics.plan.md` và file plan này | ⬜ | |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E9 | Đợt |
|---|---|---|---|
| Kiểm định 21 tiêu chí | ⬜ | ✅ | A |
| Serial và CO/CQ | ⬜ | ✅ | B |
| Ma trận 62 × 4 × 3 | ⬜ | ✅ | C |
| 240+ biên bản .docx | ⬜ | ✅ (chờ Q1) | D |
| Seed Lâm Đồng | 🟡 | ✅ | K2 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Không có file mẫu biên bản, đợt D không kiểm được thể thức | Q1. Đợt D bị chặn, các đợt khác vẫn làm được |
| CAO | Excel serial từ nhà thầu sai định dạng hoặc có dòng trùng | B1, B4: từ chối cả file, báo rõ dòng lỗi |
| CAO | Lệch số đơn vị (60 hay 62) làm sai ma trận | Q3 trước đợt C |
| TB | Sinh 248 file chậm hoặc timeout | Job theo lô, ARQ (Q4), ghi tiến độ |
| TB | Chưa có DDL cho `sample_inspections` và `delivery_batch_items` | Q2 |
| TB | Phạm vi quá lớn, dễ trễ hạn cấp tốc | Chia 4 đợt, mỗi đợt giao được riêng |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 6, Màn hình 5.3 và DDL. Phát hiện S1–S7. Chưa viết mã. Đợt D chờ Q1 |
| 2026-11-01 | Tạo `feat/e09-goods` từ `main`. TDD phần thuần: `sample_criteria.py` (A2, số tiêu chí là tham số), `serial_shortage_rules.py` (B1 phần thuần, B2, B3). Unit 174 xanh, ruff sạch. **Chưa làm:** model và migration (A3, B5, C3) vì chưa có PostgreSQL để kiểm round-trip; service và API (A4, C4); Excel (B4); ma trận (C1, C2) chờ Q3; đợt D chờ Q1. Chưa commit, chưa push, chưa tạo PR |
| 2026-11-01 | Q2–Q5 đã chốt (Q3 = 62 đơn vị; Q4 đợi E5; Q5 đúng). Người dùng yêu cầu tự tạo 21 tiêu chí tạm (`sample_criteria_catalog.py`). Thêm C1, C2 thuần (`delivery_matrix.py`). Unit 187 xanh, ruff sạch. Docker không chạy nên không có PostgreSQL: C3, C4, A3, A4, B5 và mọi migration **chưa làm, chưa kiểm chứng** |
| 2026-11-01 | Model và migration `c5d9a1e7f3b2` cho A3, B5, C3 (4 bảng, 7 index). Kiểm offline: `alembic heads` một head; `upgrade --sql` và `downgrade --sql` render đúng. Unit 192 xanh. **Chưa kiểm:** round-trip thật và `alembic check` (cần PostgreSQL). Chưa làm `delivery_batch_items` (không có trong mục 5) |
| 2026-11-01 | Service và API cho A4 (`/projects/{id}/equipment/catalog`, kiểm định mẫu) và C4 (`/projects/{id}/delivery-handovers`: sinh, lọc theo cụm và đợt, đổi trạng thái). Unit 198 xanh. 11 test tích hợp viết xong, skip vì thiếu DB. OpenAPI dựng được (7 operation mới). **Chưa kiểm:** test tích hợp chạy thật, round-trip migration, `alembic check` |
| 2026-11-01 | Docker có sẵn qua Colima (context `colima`). Chạy PostgreSQL 16 container `pmis-test-pg` cổng 55432. Test tích hợp 177 xanh (gồm 11 test mới của A4/C4). Round-trip migration sạch, `alembic check` không drift. Toàn bộ: 375 passed, 1 skipped, coverage 86%, ruff sạch. A3, B5, C3, A4, C4 chuyển ✅ |

## Acceptance

- [x] Plan đã ghi ra file
- [ ] Q1–Q5 đã được chốt
- [ ] Đợt A, B, C đạt điều kiện ✅ riêng
- [ ] Đợt D đạt điều kiện ✅ sau khi có file mẫu
- [ ] E9 đạt đủ điều kiện "E9 hoàn thành" ở mục 1
