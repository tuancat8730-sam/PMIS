# Kế hoạch: E8 Module CNTT (khảo sát, RTM, mâu thuẫn hợp đồng, phân hệ A–G, NFR, ATTT)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E8: L, phase 3, phụ thuộc E1, E3); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 5 (dòng 164–179), Màn hình 5.4 (dòng 534–538), DDL `it_system_modules` (dòng 479–491), §7 (8 đơn vị khảo sát, 7 phân hệ), §8 Phase 3; `CLAUDE.md` (archetype CNTT, dữ liệu khóa, không hard-code ngưỡng NFR).
**Độ phức tạp:** Lớn (nhiều thực thể, quy tắc truy vết, cổng NFR khóa mốc).
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e08-it-system`, tạo từ `main` sau khi E3 được merge.
**Phương pháp:** TDD. Quy tắc NFR và truy vết viết thuần, test không cần DB. Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E8 hoàn thành"

| Nhóm | Nội dung | Thuộc E8? |
|---|---|---|
| Bảng `it_system_modules` theo DDL spec, seed 7 phân hệ A–G | `app/models/it_system_module.py`, migration, seed | ✅ Có |
| Khảo sát cuốn chiếu: đơn vị khảo sát, trạng thái, biên bản đính kèm (tham chiếu E4/E5) | Bảng `it_survey_records` (DDL spec thiếu, chờ Q2) | ✅ Có (chờ Q2) |
| Ma trận truy vết: Phụ lục C ↔ mục SRS ↔ phân hệ ↔ kịch bản kiểm thử | Bảng `rtm_links` (chờ Q3) | ✅ Có (chờ Q3) |
| Mâu thuẫn hợp đồng: tái dùng `risk_issues` loại `CONTRACT_DISCREPANCY` của E3, kèm văn bản chốt của CĐT | `app/services/risk_issues.py` (E3), thêm trường văn bản chốt | ✅ Có |
| Chỉ tiêu NFR: ngưỡng là cấu hình, số đo là bảng riêng, hàm đánh giá đạt/không đạt | `app/core/nfr_rules.py` (thuần), `nfr_measurements` (chờ Q4) | ✅ Có |
| Cổng NFR và ATTT: chặn hoàn thành M7/M8 khi thiếu bằng chứng | Gọi từ quy tắc chặn mốc của E3 | ✅ Có |
| Pentest: số lỗi theo mức Critical/High/Medium/Low và trạng thái vá | Bảng `pentest_findings` (DDL spec thiếu, chờ Q5) | ✅ Có (chờ Q5) |
| Hồ sơ ATTT cấp độ 3 như một hồ sơ pháp lý | Tái dùng `legal_documents` của E4, không tạo bảng mới | ✅ Có (dùng E4) |
| H0–H9 của dự án CNTT | Tái dùng `hold_points` của E3 | ✅ Có (dùng E3) |
| Màn hình Khảo sát & RTM, NFR Dashboard | `apps/web` | ⏸ Sau khi API ổn định |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E8 được đánh ✅ khi:** migration round-trip sạch; seed 7 phân hệ A–G idempotent; truy vết không có mắt xích mồ côi (có test); NFR đạt/không đạt có unit test cho từng chỉ tiêu ở mục 2 và biên; cổng M7/M8 chặn đúng khi thiếu ATTT hoặc NFR (có test tích hợp); mâu thuẫn hợp đồng đóng được khi có văn bản chốt; coverage ≥ 80%; ruff sạch; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E1 và E3 | ✅ | `app/api/deps.py:106`; `app/models/hold_point.py`, `app/models/risk_issue.py`, `app/api/v1/hold_points.py`, `app/api/v1/risk_issues.py` |
| Mã định danh CR/NCR | ✅ | `app/core/record_codes.py` (E3) |
| Bảng `it_system_modules` | ⬜ | Chưa có |
| Bảng khảo sát, RTM, pentest, NFR | ⬜ | Chưa có. DDL `IT_SURVEY_RECORDS` và `IT_MODULES_NFR` chỉ có trong ERD |
| Mẫu quy tắc có ngưỡng | ✅ | `app/core/schedule_rules.py` (E3) |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Số trường mâu thuẫn: 1.670 (§1.1, §5.1 Survey) và 1.732 (KPI strip §5.1). Đã ghi là rủi ro trong `pmis-epics.plan.md` | Chốt số trước khi seed và khi đếm tiến độ khảo sát (Q1) |
| S2 | CAO | Spec ghi "mốc M7/M8 mở khóa khi có ATTT cấp độ 3" nhưng chưa rõ M7 hay M8 là mốc nào, và điều kiện đủ là gì | Hỏi Q6 |
| S3 | CAO | ERD có `IT_MODULES_NFR` nhưng DDL chỉ có `it_system_modules` với cột `nfr_metrics` JSONB. Hai thiết kế khác nhau | Hỏi Q4: chọn JSONB hay bảng riêng |
| S4 | TB | Mâu thuẫn hợp đồng: spec nêu ví dụ Backend Node.js vs .NET Core, 1.670 vs 3.500 trường, AWS vs cloud Việt Nam. Không có bảng cụ thể | Dùng `risk_issues` (E3) với loại `CONTRACT_DISCREPANCY`. Không tạo bảng riêng |
| S5 | TB | Spec yêu cầu 8 đơn vị khảo sát (§7) nhưng màn hình 5.4 ghi "6 trường + 2 phường". Số lượng khớp (8) | Ghi rõ: 6 trường và 2 phường, tổng 8 |
| S6 | THẤP | 7 phân hệ A–G có tên ở §5.4 và §7 nhưng tên không giống hệt nhau | Dùng tên trong §7 làm chuẩn (Q7) |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E3 | `hold_points`, `risk_issues`, `milestones_wbs` | Thiếu E3 thì cổng M7/M8 không có điểm gắn |
| E4 | `legal_documents` cho hồ sơ ATTT | Thiếu E4 thì không theo dõi được hồ sơ ATTT |
| Nhà thầu DTH và VietFuture | Tiến độ phân hệ, kết quả pentest | Dữ liệu do PM nhập, không có API ngoài |
| Hợp đồng Phụ lục C | Nguồn truy vết | Cần bản chuẩn để nhập RTM |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Dùng `it_system_modules` đúng DDL, `nfr_metrics` JSONB chỉ lưu ngưỡng, số đo nằm ở bảng riêng | Nếu Q4 chọn JSONB hoàn toàn, bỏ `nfr_measurements` |
| G2 | RTM là bảng liên kết, mỗi dòng nối một mắt xích với một mắt xích khác | Nếu cần đa chiều, thêm cột loại mắt xích |
| G3 | Phân hệ A–G thuộc một dự án CNTT. Không dùng chung giữa dự án | Thêm khóa chung nếu có dự án CNTT thứ hai dùng chung phân hệ |
| G4 | Tiến độ phân hệ nhập tay theo %, không tính tự động từ Git | Thêm tích hợp CI sau này nếu cần |

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Số trường chốt là 1.670 hay 1.732? | Người phụ trách dự án xác nhận. Đây là chặn chung với E2 và E12 | ✅ Đã chốt: 1.670 |
| Q2 | Cấu trúc `it_survey_records` là gì? | Một dòng cho mỗi trường hoặc phường: đơn vị, trạng thái, ngày, biên bản (tham chiếu `legal_documents`) | ✅ Đã chốt: một dòng mỗi đơn vị |
| Q3 | Cấu trúc `rtm_links` là gì? | Bốn cột tham chiếu: mục Phụ lục C, mục SRS, phân hệ, kịch bản kiểm thử. Mỗi cột là khóa hoặc mã chuỗi | ✅ Đã chốt: bốn cột mã chuỗi |
| Q4 | NFR lưu JSONB hay bảng riêng? | Ngưỡng trong JSONB của `it_system_modules`, số đo trong bảng `nfr_measurements` | ✅ Đã chốt: JSONB + bảng số đo |
| Q5 | Cấu trúc `pentest_findings`? | Một dòng cho mỗi lỗi: mức, mô tả, trạng thái vá, ngày kiểm tra lại | ✅ Đã chốt: mức, mô tả, trạng thái vá, ngày kiểm lại |
| Q6 | M7 hay M8 là mốc bị khóa bởi ATTT và điều kiện đủ là gì? | Chờ người phụ trách. Đề xuất: khóa M8 nghiệm thu, điều kiện là hồ sơ ATTT `VERIFIED_CLOSED` và pentest không còn lỗi Critical/High chưa vá | ✅ Đã chốt: khóa M8; đủ khi ATTT `VERIFIED_CLOSED` và không còn lỗi Critical/High chưa vá |
| Q7 | Tên chuẩn của 7 phân hệ A–G? | Lấy theo §7 | ⏸ Chờ người dùng gửi tên. Tạm seed là 'Phân hệ X' |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e08-it-system` từ `main` | ✅ | Tạo ngày 2026-11-01, chưa commit |
| 0.2 | Baseline test, coverage, ruff, alembic head | 🟡 | Baseline trước khi sửa: 157 unit đạt, 1 skip, ruff sạch. Chưa đo coverage và alembic head. `TEST_DATABASE_URL` chưa đặt nên test tích hợp skip |

### Pha 1: Quy tắc thuần (unit)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ NFR: CCU ≥ 3.600, phản hồi trung bình < 2 giây, tải 4G < 3 giây, báo cáo ≤ 10 giây, uptime ≥ 99,9%, RTO ≤ 4 giờ, backup lưu ≥ 30 ngày, audit ≥ 12 tháng | ✅ | `tests/unit/test_nfr_rules.py`. Đã thêm chỉ tiêu tài khoản ≥ 5.170 (có trong spec, thiếu trong plan gốc). Mỗi chỉ tiêu có test đúng biên |
| 1.2 | `app/core/nfr_rules.py`: ngưỡng là đối số, không hard-code | ✅ | Có `Comparison`, `NfrCriterion`, `evaluate_nfr`, `all_passed`. Thiếu số đo tính là không đạt |
| 1.3 | Test đỏ truy vết: mắt xích mồ côi bị phát hiện | ✅ | `tests/unit/test_rtm_rules.py` |
| 1.4 | `app/core/rtm_rules.py` | ✅ | Bốn mắt xích theo Q3 (đề xuất, chưa chốt). Mắt xích rỗng hoặc khoảng trắng là mồ côi |
| 1.5 | Test đỏ cổng M7/M8: thiếu ATTT hoặc có lỗi Critical chưa vá thì không cho hoàn thành | ✅ | `tests/unit/test_it_gate_rules.py`. Cổng M8 cũng chặn khi NFR chưa đạt |

### Pha 2: Mô hình và migration
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Model `ItSystemModule` theo DDL, `module_code` unique trong dự án | ✅ | `app/models/it_system_module.py`, unique (project_id, module_code) |
| 2.2 | Model `ItSurveyRecord`, `RtmLink`, `PentestFinding`, `NfrMeasurement` (sau Q2 đến Q5) | ✅ | Đúng theo Q2–Q5. Trạng thái lưu dạng chuỗi |
| 2.3 | Migration và downgrade, kiểm tra round-trip | 🟡 | Migration `c9e4a2f1b7d3`. Đã kiểm `upgrade/downgrade --sql` offline. Chưa chạy trên PostgreSQL thật (máy không có DB) |

### Pha 3: Service, router và seed
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Seed 7 phân hệ A–G và 8 đơn vị khảo sát, idempotent | 🟡 | `app/db/seed_it_system.py`: 8 đơn vị từ `hcm_survey_units.json`, 7 phân hệ tên tạm 'Phân hệ X' (chờ Q7). Chưa chạy trên DB |
| 3.2 | Test đỏ IT: tạo phân hệ, cập nhật tiến độ, 403, 404, 409 khi trùng mã, 429 | 🟡 | Đã có test unit schema (`test_it_system_schemas.py`). Chưa viết test tích hợp 403/404/409/429 |
| 3.3 | Test đỏ IT: `CONTRACT_DISCREPANCY` đóng khi có văn bản chốt | 🟡 | Test unit `test_contract_discrepancy_rules.py` xanh. Chặn trong PATCH risk-issues. Chưa có test tích hợp |
| 3.4 | Service và router mẫu E3, audit cùng transaction | ✅ | `services/it_system.py`, `services/it_gate.py`, `api/v1/it_system.py`, `api/v1/it_system_quality.py`. Router commit sau audit |
| 3.5 | Nối cổng NFR và ATTT vào quy tắc chặn mốc của E3 | ✅ | `services/milestones.py::_check_it_gate` (chỉ M8, dự án IT_SYSTEM). Hồi quy tích hợp E3 chưa chạy |

### Pha 4: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Ruff, pytest --cov ≥ 80%, `alembic check` | 🟡 | Ruff sạch. 207 unit đạt. Chưa đo coverage, chưa `alembic check`, chưa chạy integration |
| 4.2 | Đối chiếu seed với §7 và số trường (Q1) | 🟡 | 8 đơn vị khớp file seed. 1.670 chưa có bảng nào lưu nên không kiểm được tự động. Tên phân hệ chờ Q7 |
| 4.3 | Cập nhật `pmis-epics.plan.md` và file plan này | ✅ | File plan này đã cập nhật. `pmis-epics.plan.md` chưa cập nhật |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E8 | Pha |
|---|---|---|---|
| Phân hệ A–G | 🟡 (seed có, tên chờ Q7) | ✅ | 2, 3 |
| Khảo sát cuốn chiếu | 🟡 (bảng, API, seed 8 đơn vị) | ✅ | 2, 3 |
| RTM | 🟡 (quy tắc thuần xong; chưa có bảng) | ✅ (chờ Q3) | 1, 2 |
| Mâu thuẫn hợp đồng | 🟡 (quy tắc và chặn PATCH xong) | ✅ | 3 |
| NFR | 🟡 (quy tắc thuần xong; chưa nối cổng, chưa có bảng số đo) | ✅ | 1, 3 |
| ATTT và pentest | 🟡 (cổng M8, bảng và API xong; chưa test tích hợp) | ✅ | 1, 3 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Chưa rõ mốc nào bị khóa bởi ATTT (S2) | Q6 trước Pha 1.5 |
| CAO | Số trường mâu thuẫn làm sai tiến độ khảo sát | Q1 trước khi seed |
| TB | Thiết kế NFR khác ERD và DDL | Q4 |
| TB | Sửa quy tắc chặn mốc của E3 có thể làm hỏng E3 | Test hồi quy E3 chạy cùng |
| THẤP | Tên phân hệ A–G không thống nhất | Q7 |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 5, Màn hình 5.4 và DDL `it_system_modules`. Phát hiện S1–S6. Chưa viết mã |
| 2026-11-01 | Tạo nhánh `feat/e08-it-system`. Baseline: 157 unit đạt, ruff sạch. Pha 1 (1.1–1.4) xong theo TDD: RED do lỗi import, GREEN, sau đó 181 unit đạt, ruff sạch. Chưa làm 1.5 (chờ Q6), Pha 2 (chờ Q2–Q5), Pha 3 (chờ Q1, Q7 và Pha 2). Chưa commit, chưa push, chưa tạo PR |
| 2026-11-01 (tiếp) | Q1–Q6 đã chốt. Làm Pha 1.5, Pha 2 (model, migration), Pha 3 (service, router, seed, hook E3), Pha 4 (unit). 207 unit đạt, ruff sạch. Chưa chạy được integration và migration trên DB thật. Chưa commit, chưa push, chưa tạo PR |

## Acceptance

- [x] Plan đã ghi ra file
- [ ] Q1–Q7 đã được chốt
- [ ] E8 đạt đủ điều kiện "E8 hoàn thành" ở mục 1
