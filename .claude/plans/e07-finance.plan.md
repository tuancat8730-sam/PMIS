# Kế hoạch: E7 Tài chính (đa hợp đồng, bảo lãnh, tạm ứng, giải ngân)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E7: M, phase 2, phụ thuộc E1); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 7 (dòng 199–204), §7 (giá trị hợp đồng); `CLAUDE.md`.
**Độ phức tạp:** Trung bình.
**Ngày lập:** 2026-10-31. **Cập nhật:** 2026-11-01 (sau khi người dùng chốt Q1–Q4).
**Nhánh:** `feat/e07-finance`, tạo từ `main`. Chưa commit (chỉ commit khi có yêu cầu).
**Phương pháp:** TDD. Mỗi việc có test đỏ trước, rồi code tối thiểu.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E7 hoàn thành"

| Nhóm | Nội dung | Trạng thái |
|---|---|---|
| Đa hợp đồng trong một dự án | Cột `contracts.package_kind` (MAIN / CONSULTING), mặc định MAIN | ✅ |
| Bảo lãnh thực hiện HĐ | Bảng `contract_guarantees`, tỷ lệ theo `finance_rules`, chụp giá trị gốc (Q1), cờ POA hết hạn trước ngày ký | ✅ |
| Tạm ứng | Bảng `contract_advances`, trần theo tỷ lệ, 409 khi vượt trần, cờ `on_time` theo ngày làm việc (Q4) | ✅ |
| Kế hoạch vốn và giải ngân | Bảng `disbursements` (Q2), ghi nhận thanh toán, tỷ lệ giải ngân, cảnh báo vượt kế hoạch | ✅ |
| Khóa sổ Kho bạc | Ngày khóa sổ và số ngày cảnh báo theo phiên bản `finance_rules` (Q3), đếm ngược trên dòng giải ngân | ✅ |
| Đếm ngược hợp đồng và cảnh báo 30 ngày | Cho E12 | ⬜ Chưa làm (xem mục 11) |
| Seed giá trị hợp đồng và đối chiếu §7 | Dự án SGD-HCM (3 hợp đồng) | ✅ |
| Seed dự án SGD-LD-TB10-2026 | Hiện seed chưa có dự án này (ngoài phạm vi E7) | ⬜ Chưa làm |
| Màn hình tài chính trên web | `apps/web` | ⏸ Sau khi API ổn định |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

## 2. Quyết định đã chốt (Q1–Q4)

| # | Câu hỏi | Quyết định | Áp dụng ở đâu |
|---|---|---|---|
| Q1 | 3% bảo lãnh tính trên giá trị nào? | Giá trị HĐ gốc, chụp vào cột `base_contract_value` lúc phát hành | `ContractGuarantee`, `services/finance.py::create_guarantee` |
| Q2 | Cấu trúc `disbursements`? | Cấu trúc đề xuất, một dòng mỗi hợp đồng mỗi năm (`uq_disbursements_contract_year`) | Model + migration `f7a1d3c9e2b4` |
| Q3 | Ngày khóa sổ áp dụng cho đâu? | Theo dự án, lưu trong `finance_rules.lock_on`, cảnh báo `lock_warning_days` (15) | `FinanceRule`, `disbursement_rules.lock_warning_active` |
| Q4 | 20 ngày làm việc tính từ đâu? | Từ `complete_packet_on` (ngày nhận đủ hồ sơ) đến `decided_on` | `AdvanceCreate`, `advance_rules.is_advance_on_time` |

## 3. Phát hiện từ rà soát spec (vẫn mở)

| ID | Mức | Phát hiện | Trạng thái |
|---|---|---|---|
| S1 | CAO | 3% trên giá trị nào khi có phụ lục | ✅ Đã chốt Q1 |
| S2 | CAO | Spec thiếu DDL giải ngân | ✅ Đã chốt Q2 |
| S3 | TB | 20 ngày tính từ đâu | ✅ Đã chốt Q4 |
| S4 | TB | Ngày khóa sổ áp dụng cho dự án nào | ✅ Đã chốt Q3 |
| S5 | TB | Spec ghi "111,8+ tỷ" ở §5.1, nhưng tổng gói chính hai dự án là 111,073 tỷ; cộng tư vấn là 112,187 tỷ. Dự án 2 chưa có trong seed nên chưa đối chiếu được | ⏸ Cần người phụ trách xác nhận trước khi dùng cho E12 |
| S6 | THẤP | TMĐT SGD-HCM `5.999.498.939 đ` so với tổng gói | ⬜ Chưa kiểm tra (kiểm tra mềm, chưa làm) |

## 4. Giả định đang áp dụng

| # | Giả định | Ghi chú |
|---|---|---|
| G1 | Một HĐ có thể có nhiều bảo lãnh (quan hệ một-nhiều, chưa ràng buộc duy nhất) | Không đổi |
| G2 | Tỷ lệ giải ngân = tổng đã giải ngân / kế hoạch năm, làm tròn 2 chữ số | Không đổi |
| G3 | Ngưỡng nằm trong bảng `finance_rules` theo phiên bản `effective_from` | Đã làm |
| G4 | Không tính lãi, không tính phạt bảo lãnh | Không đổi |

## 5. Thay đổi so với đề xuất ban đầu

| Mục | Đề xuất ban đầu | Đã làm | Lý do |
|---|---|---|---|
| `contract_guarantees.status` | Có cột trạng thái | Bỏ, suy ra từ `expires_on` | Cột không có hành vi riêng, tránh hai nguồn sự thật |
| `contract_advances.status` | Có cột trạng thái | Bỏ | Tương tự |
| `disbursements.kho_bac_lock_on` | Cột trên từng dòng | Chuyển vào `finance_rules.lock_on` | Q3 chọn cấu hình theo dự án |
| Cờ POA | Cờ | Cờ `poa_expired_before_issue` trên `GuaranteeOut` (không chặn) | Khớp với plan 1.1 |
| Tạm ứng quá hạn 20 ngày | Quá hạn | Cờ `on_time=false` (không chặn) | Spec không nói phải chặn |
| Vượt kế hoạch giải ngân | Cảnh báo | Cờ `exceeds_plan` (không chặn) | Khớp với 2.3 |

## 6. Thiết kế đã triển khai

**Bảng và migration:** `20261101_f7a1d3c9e2b4_tao_bang_e7_tai_chinh.py` (head trước đó `e8b2c5f1a3d4`).
- `finance_rules`: ngưỡng theo phiên bản (`guarantee_percent`, `advance_ceiling_percent`, `advance_working_days`, `lock_on`, `lock_warning_days`, `non_working_days`, `effective_from`).
- `contract_guarantees`, `contract_advances`, `disbursements`: tiền là `NUMERIC(18,2)`, có `CHECK >= 0`.
- `contracts.package_kind`: `VARCHAR(20)`, mặc định `MAIN`.

**Quy tắc thuần (không chạm DB):**
- `app/core/money.py`: `percent_of`, làm tròn nửa lên về đồng lẻ 2 chữ số.
- `app/core/guarantee_rules.py`, `app/core/advance_rules.py`, `app/core/disbursement_rules.py`.

**API (đều có rate limit cho ghi, audit trong cùng transaction, service không commit):**
- `POST/GET /projects/{id}/finance-rules` (ghi: PM).
- `POST/GET /projects/{id}/contracts/{cid}/guarantees`, `POST/GET .../advances` (ghi: PM; 409 khi vượt trần tạm ứng; 422 khi chưa có ngưỡng hiệu lực).
- `POST/GET /projects/{id}/disbursements`, `POST /projects/{id}/disbursements/{did}/payments`.

**Seed:** `app/db/seed_data/hcm_contracts.json`, nạp qua `ensure_contracts` (idempotent theo tên gói).

## 7. Kế hoạch thực hiện (kết quả)

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e07-finance` từ `main` | ✅ | Nhánh `feat/e05-drive` giữ nguyên |
| 0.2 | Baseline test, coverage, ruff, alembic head | ✅ | Head trước: `e8b2c5f1a3d4`. Postgres 16 chạy trong container `pmis-pg-test` |

### Pha 1: Quy tắc thuần (unit)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ bảo lãnh | ✅ | `tests/unit/test_guarantee_rules.py` |
| 1.2 | `guarantee_rules.py` | ✅ | |
| 1.3 | Test đỏ tạm ứng: trần, 20 ngày, ngày nghỉ | ✅ | `tests/unit/test_advance_rules.py` |
| 1.4 | `advance_rules.py` | ✅ | |
| 1.5 | Test đỏ giải ngân | ✅ | `tests/unit/test_disbursement_rules.py` |
| 1.6 | `disbursement_rules.py` | ✅ | |

### Pha 2: Mô hình và migration
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Mở rộng `contracts` (`package_kind`) | ✅ | Có downgrade. Test: `tests/unit/test_contract_package_kind.py` |
| 2.2 | Model `ContractGuarantee`, `ContractAdvance`, `Disbursement`, `FinanceRule` | ✅ | Khác mục 5 |
| 2.3 | Ràng buộc `amount >= 0`; vượt kế hoạch chỉ cảnh báo | ✅ | |

### Pha 3: Service, router và seed
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ IT: bảo lãnh, trần tạm ứng (409), giải ngân, 403, 404, 422, audit | ✅ | `tests/integration/test_finance_api.py` (12 test). 429 chưa có test riêng (dùng chung `WriteRateLimitDep` của E1) |
| 3.2 | Service không commit, router có audit và rate limit | ✅ | |
| 3.3 | Đối chiếu seed với §7 | 🟡 | SGD-HCM: 3 hợp đồng khớp §7 (`tests/integration/test_seed_contracts.py`). SGD-LD chưa có trong seed |

### Pha 4: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Ruff, pytest --cov ≥ 80%, `alembic check`, round-trip migration | ✅ | Ruff sạch. Coverage 85,49%. Round-trip sạch. `alembic check` sạch |
| 4.2 | Tự review: không float trong tiền, không hard-code ngưỡng | ✅ | Đã grep `float` ở các file tài chính: không có. Ngưỡng đều đến từ `finance_rules` |
| 4.3 | Cập nhật `pmis-epics.plan.md` và file này | ✅ | |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E7 | Kết quả |
|---|---|---|---|
| Đa hợp đồng | ✅ | ✅ | `package_kind` |
| Bảo lãnh | ✅ | ✅ | |
| Tạm ứng | ✅ | ✅ | |
| Giải ngân và tỷ lệ | ✅ | ✅ | |
| Đối chiếu số liệu §7 | 🟡 | ✅ | Chỉ SGD-HCM |

## 9. Kết quả kiểm chứng

- Unit: 93 passed. Tích hợp (Postgres 16 thật): toàn bộ suite 225 passed, 1 skipped.
- Coverage: 85,49% (ngưỡng 80%).
- Ruff check và format: sạch.
- `alembic upgrade head`, `alembic check`, `downgrade -1`, `upgrade head`: sạch.

## 10. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Số liệu 111,8 tỷ (S5) sai đưa vào báo cáo | Cần xác nhận trước E12 |
| TB | Tạm ứng song song vượt trần | `SELECT ... FOR UPDATE` trên dòng hợp đồng, đã làm. Chưa có test đồng thời |
| TB | Quy định ngày nghỉ thay đổi | `non_working_days` theo phiên bản `finance_rules` |
| THẤP | Seed Lâm Đồng chưa có | Ngoài E7, cần làm ở E2 hoặc việc riêng |

## 11. Còn lại (chưa làm)

1. Đếm ngược hợp đồng và cảnh báo 30 ngày (dữ liệu cho E12).
2. Seed dự án SGD-LD-TB10-2026 và đối chiếu §7 phần Lâm Đồng.
3. Kiểm tra mềm TMĐT với tổng gói (S6).
4. Test đồng thời cho trần tạm ứng.
5. Màn hình web tài chính (⏸).

## 12. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 7 và §7. Phát hiện S1–S6 |
| 2026-11-01 | Người dùng chốt Q1–Q4 theo đề xuất. Tạo `feat/e07-finance`. Viết test đỏ rồi code cho quy tắc thuần, model, migration, API, seed. Toàn bộ suite xanh trên Postgres thật |

## Acceptance

- [x] Plan đã ghi ra file
- [x] Q1–Q4 đã được chốt
- [ ] E7 đạt đủ điều kiện "E7 hoàn thành" ở mục 1 (còn mục 11)
