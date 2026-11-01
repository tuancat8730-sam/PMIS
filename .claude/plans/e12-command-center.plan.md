# Kế hoạch: E12 Command Center (KPI, thẻ cảnh báo đỏ, đếm ngược hợp đồng)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E12: M, phase 2 cơ bản rồi phase 4 đầy đủ, phụ thuộc E1–E9); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 1 mục 1 (dòng 101–108), Màn hình 5.1 (dòng 517–522), §8 Phase 2 (Executive Dashboard) và Phase 4.
**Độ phức tạp:** Trung bình. Chủ yếu là tổng hợp dữ liệu đọc, không có bảng lõi mới. Rủi ro nằm ở số liệu nguồn từ các epic khác.
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e12-command-center`, tạo từ `main`. Phần cơ bản làm sau E1–E3 (phase 2); phần đầy đủ làm sau E9 và E11 (phase 4).
**Phương pháp:** TDD. Quy tắc health và đếm ngược viết thuần. Phần đọc tổng hợp có test tích hợp. Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E12 hoàn thành"

| Nhóm | Nội dung | Thuộc E12? |
|---|---|---|
| Danh sách dự án với trạng thái sức khỏe `ON_TRACK`, `AT_RISK`, `DELAYED`, `CRITICAL`, `COMPLETED` | `app/core/project_health.py` (thuần), `app/services/command_center.py` | ✅ Có (phase 2) |
| KPI strip: tổng giá trị hợp đồng, số dự án đang chạy, tổng điểm thụ hưởng, hồ sơ chờ ký, số cảnh báo đỏ | `app/services/command_center.py` | ✅ Có (phase 2) |
| Thẻ cảnh báo đỏ: việc khẩn trong 48 giờ tới | `app/core/red_alert_rules.py` (thuần) | ✅ Có (phase 2) |
| Đồng hồ đếm ngược hợp đồng: gói chính 120 ngày, TVQLDA 150–180 ngày, TVGS 120–150 ngày; cảnh báo sớm 30 ngày | `app/core/contract_countdown.py` (thuần) | ✅ Có (phase 2, cần ngày hết hạn của E7) |
| Trang chủ Ban Giám đốc: đọc từ API, không ghi | `apps/web` | ⏸ Sau API |
| Xu hướng theo thời gian, biểu đồ lịch sử | — | ⏸ Phase 4 |
| Trợ lý AI điều hành (AI PM Copilot) | — | ⏸ Ngoài phạm vi, chưa có spec chi tiết |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E12 được đánh ✅ khi:**
- Phase 2: API tổng hợp trả đúng cho hai dự án seed (có test so sánh từng con số với dữ liệu nguồn); quy tắc health và đếm ngược có unit test bao gồm biên; thẻ đỏ đúng hạn 48 giờ; số truy vấn không tăng theo số dự án (không N+1, có test đếm truy vấn).
- Phase 4: có xu hướng theo thời gian và phần AI nếu được duyệt riêng.
- Chỉ đọc: không có endpoint ghi; quyền đọc theo dự án (thành viên thấy dự án của mình, ADMIN thấy tất cả).
- Coverage ≥ 80%; ruff sạch; OpenAPI cập nhật; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Dự án và quyền theo dự án | ✅ | `app/models/project.py`, `app/api/deps.py:23` `ANY_PROJECT_ROLE`, `app/api/deps.py:106` `project_role_guard` |
| Sức khỏe dự án (`project_health`) | 🟡 | Enum có trong DDL `projects` (E1). Chưa có quy tắc tính |
| Mốc và trạng thái trễ | 🟡 | `app/models/milestone.py`, `app/core/schedule_rules.py` (E3, đang làm) |
| Rủi ro và cảnh báo | 🟡 | `app/models/risk_issue.py` (E3) |
| Hồ sơ pháp lý | ⬜ | Chờ E4 |
| Hợp đồng và ngày hết hạn | 🟡 | `app/models/contract.py` (E1). Chưa có ngày hết hạn đầy đủ, chờ E7 |
| Số trường thụ hưởng | ✅ | `app/models/beneficiary_unit.py` (E2) |
| Serial và giao hàng | ⬜ | Chờ E9 |
| Mẫu API đọc | ✅ | `app/api/v1/projects.py` (E1) |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | KPI "111,8+ tỷ" (§5.1) không khớp với tổng gói ở §7. Tổng gói chính hai dự án là 111,073 tỷ. Cộng cả gói tư vấn là 112,187 tỷ | Q1: chốt số đúng. Không hard-code số 111,8 trong code |
| S2 | CAO | Số trường mâu thuẫn: 1.670 và 1.732 (đã có trong `pmis-epics.plan.md`) | Q2, cùng câu hỏi ở E8 |
| S3 | CAO | Ngưỡng `ON_TRACK`, `AT_RISK`, `DELAYED`, `CRITICAL` không có quy tắc trong spec | Q3: đề xuất ngưỡng theo số ngày trễ và số cảnh báo, lưu thành cấu hình |
| S4 | TB | Đồng hồ đếm ngược: "120 ngày" và "150–180 ngày" là khoảng thời gian, không phải ngày hết hạn. Cần ngày bắt đầu để tính | Lấy ngày hiệu lực và thời hạn từ E7 (Q4) |
| S5 | TB | Thẻ đỏ mẫu "Thiếu 1.100/1.420 số Serial" phụ thuộc E9. Phase 2 chưa có số này | Phase 2 bỏ qua thẻ này, phase 4 thêm |
| S6 | THẤP | Trang chủ có "Hồ sơ chờ ký 14 văn bản" (§5.1). Số này cần E4 | Phase 2 hiển thị "chưa có dữ liệu", không hiển thị số giả |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E1 | Dự án, hợp đồng, quyền | Đã có |
| E2 | Đơn vị thụ hưởng | Đã có một phần |
| E3 | Mốc, rủi ro, H0–H9 | Đang làm, đã có API |
| E4 | Hồ sơ pháp lý | Chưa có |
| E7 | Ngày hiệu lực hợp đồng, bảo lãnh | Chưa có |
| E9 | Serial, giao hàng | Chưa có |
| E11 | Báo cáo | Chưa có. Không cần cho phase 2 |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Trang tổng quan là API chỉ đọc, không có bảng riêng | Nếu cần lưu cấu hình ngưỡng theo dự án, thêm bảng cấu hình |
| G2 | Health tính khi đọc, không lưu cứng | Lưu snapshot nếu cần xu hướng (phase 4) |
| G3 | Ngưỡng nằm trong cấu hình có phiên bản, mặc định theo đề xuất Q3 | Đổi qua cấu hình |
| G4 | Số liệu thiếu hiển thị "chưa có dữ liệu", không hiển thị 0 | Nếu PM muốn 0, đổi ở tầng trình bày |

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Tổng giá trị hợp đồng hiển thị là bao nhiêu: 111,8 tỷ (spec), 111,07 tỷ (chỉ gói chính), hay 112,19 tỷ (cả tư vấn)? | Người phụ trách xác nhận. Code tính từ dữ liệu, không hard-code | ✅ Người dùng chọn: tính từ dữ liệu, tách theo gói MAIN / CONSULTING |
| Q2 | Số trường chốt là 1.670 hay 1.732? | Cùng câu hỏi Q1 của E8 | ⏸ Chờ người dùng |
| Q3 | Ngưỡng health là gì? | Đề xuất: `CRITICAL` khi có mốc cứng trễ hoặc có hơn 3 cảnh báo đỏ; `DELAYED` khi có mốc trễ quá 7 ngày; `AT_RISK` khi có mốc trễ hoặc cảnh báo; `ON_TRACK` còn lại. Lưu thành cấu hình | ⏸ Chờ xác nhận |
| Q4 | Ngày hiệu lực và thời hạn từng gói là gì? | Lấy từ E7. Hai dự án trong spec: gói chính 120 ngày, TVQLDA 150–180 ngày, TVGS 120–150 ngày | ⏸ Chờ người dùng |
| Q5 | Cảnh báo đỏ 48 giờ dùng nguồn nào? | Tổng hợp từ hạn mốc, hạn rủi ro, hạn đôn đốc hồ sơ (E4), hết hạn bảo lãnh (E7) | ⏸ Chờ xác nhận |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e12-command-center` từ `main` | ⬜ | |
| 0.2 | Baseline test, coverage, ruff | ⬜ | |

### Pha 1: Quy tắc thuần (phase 2)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ health: bốn ngưỡng và biên | ✅ | `tests/unit/test_project_health_rules.py` (10 test) |
| 1.2 | `app/core/project_health.py` | ✅ | Ngưỡng là `HealthThresholds` (mặc định theo Q3, chưa được PM chốt) |
| 1.3 | Test đỏ đếm ngược: còn 30 ngày thì cảnh báo, còn 31 ngày thì không | ✅ | `tests/unit/test_contract_countdown_rules.py` |
| 1.4 | `app/core/contract_countdown.py` | ✅ | Chỉ dùng `expiration_date` của hợp đồng; thời hạn 120/150 ngày chờ E7 (Q4) |
| 1.5 | Test đỏ thẻ đỏ: việc đến hạn trong 48 giờ có thẻ, quá 48 giờ không có | ✅ | `tests/unit/test_red_alert_rules.py`. Quá hạn cũng đỏ (G5) |
| 1.6 | `app/core/red_alert_rules.py` | ✅ | Đo theo ngày: 48 giờ = 2 ngày lịch (G5) |

### Pha 2: API tổng hợp (phase 2)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ IT: KPI và danh sách dự án đúng với dữ liệu test | ✅ | `tests/integration/test_command_center_api.py::test_admin_kpi_sums_contracts_and_counts_red_milestones`. Dùng dữ liệu tạo trong test, chưa dùng seed hai dự án (Q2 chưa chốt nên không hard-code số) |
| 2.2 | Test đỏ IT: người không thuộc dự án không thấy dự án đó (403 hoặc lọc) | ✅ | `test_member_sees_only_projects_they_belong_to`. Lọc theo thành viên, không trả 403 |
| 2.3 | Test đếm truy vấn: số truy vấn không tăng theo số dự án | ✅ | `test_query_count_does_not_grow_with_project_count` (1 dự án và 4 dự án cho cùng số truy vấn) |
| 2.4 | `app/services/command_center.py`: gom số liệu bằng vài truy vấn GROUP BY | ✅ | 5 truy vấn cố định: danh sách dự án, mốc, rủi ro mở, hợp đồng, số thụ hưởng (group by) |
| 2.5 | Router `GET /api/v1/command-center`, chỉ đọc | ✅ | `app/api/v1/command_center.py`; `test_endpoint_is_read_only` đọc OpenAPI; `test_unauthenticated_request_is_rejected` |

### Pha 3: Giao diện trang chủ (phase 2)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ (Vitest) hiển thị KPI và thẻ đỏ từ dữ liệu | ✅ | `src/components/command-center/command-center-view.test.tsx` (3 test), `src/lib/command-center.test.ts` (6 test). Thêm `vitest.config.mts` để JSX tự động |
| 3.2 | Trang chủ và bộ chuyển dự án (Project Switcher) | ✅ | Đặt ở `/command-center`, không thay trang `/` (trang `/` vẫn hiện trạng thái API). Bộ chọn dự án là `<select>`. Tiếng Việt, vi-VN. `next build` xanh, trang 119 kB gzip |

### Pha 4: Phase 4 đầy đủ (sau E9, E11)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Thẻ đỏ có serial thiếu hụt và chưa có QĐ tổ nghiệm thu (E9) | ⏸ | Chờ E9 |
| 4.2 | Hồ sơ chờ ký có số liệu thật (E4) | ⏸ | Chờ E4 |
| 4.3 | Xu hướng theo thời gian (snapshot hằng ngày) | ⏸ | Có quyết định riêng |

### Pha 5: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Ruff, pytest --cov ≥ 80%, lint và test web | ⬜ | |
| 5.2 | Kiểm chỉ đọc: không có endpoint ghi trong router | ⬜ | |
| 5.3 | Cập nhật `pmis-epics.plan.md` và file plan này | ⬜ | |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E12 phase 2 | Đích E12 phase 4 | Pha |
|---|---|---|---|---|
| Sức khỏe dự án | ⬜ | ✅ | ✅ | 1, 2 |
| KPI strip | ⬜ | ✅ (hồ sơ chờ ký hiển thị "chưa có dữ liệu") | ✅ | 2 |
| Thẻ cảnh báo đỏ | ⬜ | ✅ | ✅ (đủ nguồn) | 1, 4 |
| Đồng hồ đếm ngược | ⬜ | ✅ | ✅ | 1 |
| Xu hướng | ⬜ | ⏸ | ✅ | 4 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Số liệu KPI sai, lệch với các con số đã biết (111,8 tỷ, 1.670 hay 1.732) | Q1, Q2 trước khi lên trang chủ. Test so sánh với seed |
| CAO | Ngưỡng health không được PM đồng ý, trang chủ gây hiểu lầm | Q3, cấu hình có thể đổi |
| TB | Truy vấn chậm khi có nhiều dự án | Gom GROUP BY, test đếm truy vấn |
| TB | Hiển thị số 0 cho dữ liệu chưa có, gây hiểu lầm | G4: hiển thị "chưa có dữ liệu" |
| THẤP | Trang đọc dữ liệu từ nhiều epic, đổi cấu trúc ở một epic làm vỡ trang chủ | Test hồi quy theo từng nguồn |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 1 mục 1 và Màn hình 5.1. Phát hiện S1–S6. Đối chiếu tổng giá trị hợp đồng với §7. Chưa viết mã |
| 2026-11-01 | Pha 1 xong theo TDD (RED → GREEN): 22 test, ruff sạch, toàn bộ unit test 297 passed. Pha 2 (API tổng hợp) và Pha 3 (giao diện) chưa làm: chờ Q1, Q2, Q3, Q4 và chưa có Postgres để chạy integration test. Ngưỡng health và cửa sổ 48 giờ là đề xuất, chưa được chốt |
| 2026-11-01 | Pha 2 xong theo TDD: service gom dữ liệu bằng 5 truy vấn cố định, router chỉ đọc, 5 test integration xanh trên Postgres 16 (Docker, cổng 55433, DB `pmis_test`). Phạm vi xem: ADMIN thấy tất cả, còn lại theo thành viên (người dùng chọn). Tổng HĐ tính từ dữ liệu, tách theo gói (người dùng chọn). Chưa làm: Pha 3 (giao diện), Pha 4. Q2 (1.670 hay 1.732) chưa chốt, nên số trường lấy từ bảng thụ hưởng, không hard-code |
| 2026-11-01 | Pha 3 xong: trang `/command-center` (Client, đọc token từ khóa `pmis.field.token`), component trình bày thuần, lọc theo dự án. Vitest 31 test xanh, tsc và eslint sạch, `next build` xanh. Chưa làm: Pha 4 (chờ E9, E4, và xu hướng cần quyết định riêng). Chưa có kiểm thử trình duyệt thật (Playwright) |

## Acceptance

- [x] Plan đã ghi ra file
- [ ] Q1–Q5 đã được chốt
- [ ] Phase 2 đạt điều kiện ✅ ở mục 1
- [ ] Phase 4 đạt điều kiện ✅ sau E9, E11
