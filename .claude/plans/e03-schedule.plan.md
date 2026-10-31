# Kế hoạch: E3 Tiến độ (baseline kép, đường găng, slippage, phạt, H0–H9, CR/NCR, rủi ro)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E3: L, phase 2, phụ thuộc E1, E2); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 4 (dòng 152–162), DDL `milestones_wbs` (dòng 367–391), DDL `project_risks_and_issues` (dòng 493–511), §7 seed M1–M9, §8 Phase 2; `CLAUDE.md` (layering, service không commit, audit cùng transaction, dữ liệu khóa, không hard-code ngưỡng, TDD, AAA).
**Độ phức tạp:** Lớn (Large). Ba bảng mới, nhiều quy tắc nghiệp vụ, một mục spec còn mơ hồ (xem mục 6).
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e03-schedule` tạo từ `main` (sau khi E2 đã merge qua PR #3).
**Phương pháp:** rà soát tĩnh `apps/api` và đối chiếu spec. Thực hiện theo TDD: test đỏ → xanh → refactor. Chưa viết mã; plan này chờ người dùng xác nhận các quyết định ở mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E3 hoàn thành"

| Nhóm | Nội dung | Thuộc E3? |
|---|---|---|
| Bảng `milestones_wbs` theo DDL spec: baseline và adjusted, mốc cứng, tiến độ, trạng thái, mã H và CL | `app/models/milestone.py`, migration mới | ✅ Có |
| Bảng `hold_points` (H0–H9) và xác nhận 3 bên (CĐT, TVGS, Nhà thầu) kèm evidence | `app/models/hold_point.py`, migration mới | ✅ Có |
| Bảng `project_risks_and_issues` cho RISK, ISSUE, CR, NCR, CONTRACT_DISCREPANCY | `app/models/risk_issue.py`, migration mới | ✅ Có |
| Lưu bản ghi điều chỉnh khi đổi mốc đã khóa (không sửa trực tiếp) | `app/models/milestone_adjustment.py` | ✅ Có (CLAUDE.md, dữ liệu khóa) |
| Tính slippage và mức phạt; ngưỡng phạt lưu theo cấu hình có phiên bản | `app/core/schedule_rules.py` (thuần, không DB) | ✅ Có |
| Chặn hoàn thành mốc khi H_x chưa đủ evidence và đủ 3 xác nhận | `app/services/hold_points.py` | ✅ Có (spec Phân hệ 4 mục 2) |
| Đường găng | Spec không có quan hệ tiền nhiệm (xem mục 6, Q2) | ⏸ Chờ quyết định Q2 |
| Mã định danh CR/NCR tự sinh (VD `CRY-SGD-NCR-001`) | `app/services/risk_issues.py` | ✅ Có, theo format đã chốt ở Q4 |
| API CRUD và đọc tiến độ theo dự án | `app/api/v1/milestones.py`, `hold_points.py`, `risk_issues.py` | ✅ Có |
| Seed M1–M9 cho SGD-HCM (baseline, M1 điều chỉnh 07/10 → 05/11, M8 30/11 và M9 09/12 cứng) | `app/db/seed_real_projects.py` | ✅ Có, kiểm tra dữ liệu ở Pha 5 |
| Seed DOT_1–DOT_3 và M1–M9 cho SGD-Lâm Đồng | Cùng script | ⏸ Chờ dữ liệu, cùng hướng B1 của E2 |
| Gantt và màn hình web | `apps/web` | ⏸ Làm sau khi API ổn định, như E2 |
| Báo cáo tuần, dashboard cảnh báo đỏ | — | ⏸ E11, E12 |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu (CLAUDE.md) |

**E3 được đánh ✅ khi:** migration round-trip sạch, `alembic check` không drift; API có test xanh (đọc, ghi, 403, 404, 409, audit, 429 ở endpoint ghi); quy tắc slippage, phạt, chặn mốc và mốc cứng có unit test; seed M1–M9 SGD-HCM idempotent; coverage ≥ 80%; ruff sạch; OpenAPI cập nhật; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E1 (dự án, quyền theo dự án) | ✅ | `app/api/deps.py` có `project_role_guard`, `ANY_PROJECT_ROLE` |
| Phụ thuộc E2 (đơn vị thụ hưởng) | ✅ | Đã merge (`f5351c7`, PR #3). Lưu ý: bảng `pmis-epics.plan.md` vẫn ghi "Đang làm", cần cập nhật ở Pha 6 |
| Bảng `milestones_wbs` | ⬜ | Chưa có model. Migration head hiện tại: `2a5dbfd319bf` hoặc `72cef211f6aa` (kiểm tra bằng `alembic heads` ở Pha 0) |
| Bảng `hold_points`, `project_risks_and_issues` | ⬜ | Chưa có model |
| Mẫu model | ✅ | `app/models/contract.py:1-30`: `Mapped`, `mapped_column`, `text("gen_random_uuid()")`, `Numeric(18, 2)` cho tiền |
| Mẫu service (không commit) | ✅ | `app/services/contracts.py:8-18` `create_contract` chỉ `session.add` và `flush`; commit nằm ở router |
| Mẫu router ghi | ✅ | `app/api/v1/contracts.py:15-35`: `project_role_guard(Role.PM)`, `WriteRateLimitDep`, `record_audit`, `session.commit()` |
| Mẫu test tích hợp | ✅ | `tests/integration/test_contracts_api.py:1-40`: `pytestmark = pytest.mark.integration`, AAA, helper `create_project`, `login_as`, `make_user` |
| Mẫu test đơn vị thuần | ✅ | `tests/unit/test_personnel_rules.py`, `tests/unit/test_beneficiary_units_rules.py` (quy tắc tách khỏi DB) |
| Enum | ✅ | `app/models/project.py:12-16` `StrEnum` + `enum_values` (lưu UPPER_SNAKE) |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Spec yêu cầu "Đường găng" nhưng `milestones_wbs` chỉ có `parent_id` (cấu trúc cây), không có quan hệ tiền nhiệm | Hỏi Q2 trước khi làm |
| S2 | CAO | Mức phạt "0,1%/ngày, tối đa 8%" nhưng spec không nói cơ số tính phạt (giá trị hợp đồng, giá trị phần việc chậm, hay giá trị mốc) | Hỏi Q1 |
| S3 | TB | Spec tự mâu thuẫn về dữ liệu: `milestones_wbs.status` có `OVERDUE` nhưng `AT_RISK` và `OVERDUE` có thể suy ra từ slippage. Nếu lưu cứng thì dễ lệch | Trạng thái trễ tính lúc đọc từ ngày, không lưu. Chỉ lưu trạng thái do người dùng chọn |
| S4 | TB | `hold_point_code` nằm trong mốc, nhưng xác nhận 3 bên cần nhiều dòng (mỗi bên một người, một thời điểm, evidence riêng). Một cột không đủ | Thêm bảng `hold_points` theo dự án và mã H, tham chiếu từ mốc (xem Q3) |
| S5 | TB | Mã CR/NCR trong spec có hai dạng: `CRY-SGD-NCR-001`, `CR-20261016` | Hỏi Q4 |
| S6 | THẤP | Spec gọi `M8` và `M9` là mốc cứng, nhưng cột `is_hard_deadline` do seed đặt, không có ràng buộc | Thêm kiểm tra: không cho `adjusted_end` vượt `baseline_end` của mốc cứng. Ngoại lệ phải có bản ghi điều chỉnh có lý do |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E1 | `projects`, `project_role_guard` | Bắt buộc |
| E2 | `beneficiary_units` (mốc có thể gắn đơn vị, tùy Q5) | Mềm: mốc không cần đơn vị ở E3 |
| Dữ liệu tiến độ SGD-HCM | Ngày M1–M9 và tên mốc lấy từ spec §3 Phân hệ 5, §7 | Phải đọc lại đoạn spec đó ở Pha 5 để điền đúng |
| Dữ liệu SGD-Lâm Đồng | DOT_1–DOT_3 chưa có ngày chốt | Chặn seed Lâm Đồng (⏸) |
| Công thức phạt | Chưa có cơ số (S2) | Chặn hoàn thiện `schedule_rules` phần phạt |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Slippage (ngày) = ngày kết thúc thực tế (hoặc hôm nay nếu chưa xong) trừ ngày kết thúc điều chỉnh (nếu có) hoặc ngày kết thúc gốc | Đổi công thức trong `schedule_rules`, một chỗ |
| G2 | Trạng thái `OVERDUE` và `AT_RISK` được suy ra khi đọc, không lưu | Nếu cần lưu, thêm job nền (ARQ, theo quyết định epic) |
| G3 | Mỗi thay đổi `adjusted_*` trên mốc đã khóa tạo một `milestone_adjustments` có lý do và người duyệt | Nếu chỉ cần audit, bỏ bảng và dùng `audit_logs` |
| G4 | Ngưỡng phạt (0,1%/ngày, 8%) lưu trong bảng `penalty_rules` có phiên bản (effective_from), không hard-code | Đổi thành cấu hình env nếu không cần lịch sử |
| G5 | Đường găng chưa làm ở E3; dừng ở mốc, slippage, cảnh báo | Nếu Q2 chọn có quan hệ tiền nhiệm, thêm bảng `milestone_dependencies` và thuật toán CPM |
| G6 | Mốc là một cây (`parent_id`), không có Gantt nhiều tầng ngoài cây đó | Không ảnh hưởng API |
| G7 | Rate limit ghi dùng `WriteRateLimitDep` như E0 (30 lần/60 giây theo IP) | Điều chỉnh qua `*_RATE_LIMIT_*` |

## 6. Quyết định (đã chốt với người dùng ngày 2026-10-31)

| # | Câu hỏi | Quyết định |
|---|---|---|
| Q1 | Cơ số tính phạt | Giá trị hợp đồng: 0,1% × số ngày chậm × giá trị hợp đồng, trần 8% giá trị hợp đồng |
| Q2 | Đường găng | Để sang đợt sau (⏸). E3 không có quan hệ tiền nhiệm, không thuật toán CPM |
| Q3 | Hold point H0–H9 | Bảng `hold_points` riêng theo dự án và mã H, ba dòng xác nhận (CĐT, TVGS, Nhà thầu), mỗi dòng có người, thời điểm, evidence |
| Q4 | Mã CR/NCR | Hệ thống tự sinh theo format `{PREFIX}-{LOẠI}-{SỐ}`, số tăng theo dự án, unique theo dự án (VD `CRY-SGD-NCR-001`). Cần chốt thêm `PREFIX` và `LOẠI` theo từng dự án khi làm Pha 3 |
| Q5 | Mốc gắn đơn vị thụ hưởng | Không ở E3, để E9 |
| Q6 | Trạng thái `OVERDUE`/`AT_RISK` | Suy ra khi đọc (G2) |

Hệ quả cho plan: Q4 đổi mục 1 (dòng mã CR/NCR, dạng tự sinh thay cho "theo format đã chốt"), Pha 1.4 (ràng buộc unique vẫn áp dụng, mã do hệ thống sinh) và Pha 3.2 (cần service sinh mã với bộ đếm an toàn khi song song). Q1 đã đúng với mặc định trong Pha 2.2.

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor. Mỗi việc ghi audit trong cùng transaction với router. Không commit.

### Pha 0 – Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Ghi plan này | ✅ | |
| 0.2 | Xác nhận Q1–Q6 | ✅ | Đã chốt, xem mục 6 |
| 0.3 | Tạo nhánh `feat/e03-schedule` từ `main` | ⬜ | |
| 0.4 | `alembic heads` xác định head; `make api-test` baseline với `TEST_DATABASE_URL` trỏ PostgreSQL 16 ở cổng 5433 (F7 của E0) | ⬜ | Kỳ vọng xanh trước khi sửa |

### Pha 1 – Model và migration (TDD qua integration)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: migration tạo `milestones_wbs`, `hold_points`, `project_risks_and_issues`, `milestone_adjustments`, `penalty_rules`; round-trip upgrade/downgrade | ⬜ | Mirror migration E1/E2: `migrations/versions/20261031_*.py` |
| 1.2 | Model `Milestone`, `HoldPoint`, `RiskIssue`, `MilestoneAdjustment`, `PenaltyRule` dùng `Mapped`, `text("gen_random_uuid()")`, enum UPPER_SNAKE | ⬜ | Mirror `app/models/contract.py` |
| 1.3 | Đăng ký trong `app/models/__init__.py`; `alembic check` không drift | ⬜ | CLAUDE.md |
| 1.4 | Ràng buộc: `UNIQUE(project_id, code)` cho mốc, `UNIQUE(project_id, hold_point_code)` cho H, `UNIQUE(project_id, code)` cho risk/issue (Q4) | ⬜ | |

### Pha 2 – Quy tắc thuần (unit, không DB)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ `tests/unit/test_schedule_rules.py`: slippage theo G1 (chưa xong, đã xong, có điều chỉnh) | ⬜ | Mirror `tests/unit/test_personnel_rules.py` |
| 2.2 | Test đỏ: phạt 0,1%/ngày, trần 8%, không phạt khi chưa trễ, cơ số theo Q1 | ⬜ | Chờ Q1 |
| 2.3 | Test đỏ: mốc cứng không được đẩy quá `baseline_end` nếu không có bản điều chỉnh | ⬜ | S6 |
| 2.4 | Test đỏ: chặn hoàn thành mốc khi H_x thiếu evidence hoặc thiếu một trong 3 xác nhận | ⬜ | Đây là quy tắc "không được tính hoàn thành mốc" trong spec |
| 2.5 | Viết `app/core/schedule_rules.py` tối thiểu cho các test đỏ; refactor; không magic number (ngưỡng nằm trong `PenaltyRule`) | ⬜ | Hàm dưới 50 dòng |

### Pha 3 – Service (không commit)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ: CRUD mốc theo dự án, đọc danh sách kèm slippage và trạng thái suy ra | ⬜ | Mirror `test_contracts_api.py` |
| 3.2 | `app/services/milestones.py`, `hold_points.py`, `risk_issues.py`, `milestone_adjustments.py` | ⬜ | Mirror `app/services/contracts.py:8-18`: chỉ `add` và `flush` |
| 3.3 | Đổi `adjusted_end` trên mốc đã khóa: bắt buộc tạo `MilestoneAdjustment` có lý do, không sửa trực tiếp | ⬜ | CLAUDE.md, dữ liệu khóa |
| 3.4 | Xử lý lỗi: mốc không tồn tại → 404, trùng mã → 409, vi phạm mốc cứng → 422 có thông điệp tiếng Việt, log chi tiết phía server | ⬜ | Mirror `app/api/v1/contracts.py` và `test_users_api.py` về 409 |

### Pha 4 – Router, schema, audit, rate limit
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ IT: PM ghi được; PM_CONSULTANT, INVESTOR chỉ đọc; CONTRACTOR không ghi; 403 và 404; audit trong cùng transaction; 429 ở ghi | ⬜ | Mirror `test_project_access.py` |
| 4.2 | Schema `app/schemas/milestones.py`, `hold_points.py`, `risk_issues.py` kế thừa `RequestModel` (`extra="forbid"`); response không có trường nội bộ | ⬜ | `app/schemas/base.py` |
| 4.3 | Router `app/api/v1/milestones.py`, `hold_points.py`, `risk_issues.py`; đăng ký trong `app/api/v1/__init__.py` | ⬜ | Mirror `contracts.py`; `WriteRateLimitDep` cho POST/PATCH |
| 4.4 | Audit: `milestone.create`, `milestone.update`, `milestone.adjust`, `hold_point.sign`, `risk_issue.create`, `risk_issue.close` | ⬜ | `services/audit.py` |

### Pha 5 – Seed SGD-HCM
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Đọc lại spec §3 Phân hệ 5 và §7 để lấy đúng M1–M9 (ngày baseline, M1 điều chỉnh 07/10 → 05/11, M8 30/11, M9 09/12) | ⬜ | Không điền từ trí nhớ |
| 5.2 | Test đỏ: seed hai lần cho ra cùng số bản ghi; M8 và M9 có `is_hard_deadline = TRUE` | ⬜ | Mirror `test_seed_real_projects.py` |
| 5.3 | Thêm vào `app/db/seed_real_projects.py` | ⬜ | Seed Lâm Đồng để ⏸ |

### Pha 6 – Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | `make api-lint`, `make api-test` với coverage ≥ 80%, `alembic check` | ⬜ | |
| 6.2 | Tự review diff: không secret, không `print`, không `.env`, không hard-code ngưỡng phạt | ⬜ | security.md |
| 6.3 | Rà soát bảo mật: auth, RBAC theo dự án, input và truy vấn DB (có quy tắc `security-reviewer` của ECC) | ⬜ | Bắt buộc theo CLAUDE.md |
| 6.4 | Cập nhật `.claude/plans/pmis-epics.plan.md` (E3 và đánh dấu E2 đã merge) và plan này | ⬜ | |
| 6.5 | Không commit; báo lại người dùng để quyết định | ⬜ | |

## 8. Trạng thái theo yêu cầu (đích cần đạt)

| Yêu cầu | Hiện tại | Đích E3 | Pha |
|---|---|---|---|
| Baseline kép (gốc và điều chỉnh) | ⬜ | ✅ | 1, 3 |
| Slippage và phạt | ⬜ | ✅ | 2, 3 |
| Mốc cứng M8, M9 | ⬜ | ✅ | 2, 5 |
| H0–H9 và 3 xác nhận | ⬜ | ✅ | 1, 2, 4 |
| CR/NCR/RISK | ⬜ | ✅ | 1, 4 |
| Đường găng | ⏸ (Q2) | ⏸ | – |
| Seed SGD-HCM | ⬜ | ✅ | 5 |
| Seed Lâm Đồng | ⏸ (dữ liệu) | ⏸ | – |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Công thức phạt sai cơ số làm sai số tiền trên hợp đồng thật | Q1 phải chốt trước Pha 2. Test theo ví dụ đã tính tay từ hợp đồng |
| CAO | Đường găng bị hiểu sai là đã có khi thực tế chưa | Ghi rõ ⏸ ở mục 1 và mục 8; Q2 |
| TB | Trạng thái suy ra lúc đọc tốn truy vấn khi số mốc lớn | Số mốc mỗi dự án nhỏ (9–12). Chỉ tối ưu khi đo thấy chậm |
| TB | Mốc cứng bị đẩy qua hạn do sửa tay | S6: ràng buộc và bản ghi điều chỉnh bắt buộc |
| TB | Ba xác nhận hold point bị ghi trùng hoặc giả mạo | Ràng buộc `UNIQUE(hold_point, party)`, audit người xác nhận, không cho một người xác nhận hai bên |
| THẤP | Trùng mã CR/NCR giữa hai dạng trong spec | Q4 |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Đọc plan epic, spec Phân hệ 4, DDL `milestones_wbs` và `project_risks_and_issues`, mẫu contract (model, service, router, test). Phát hiện S1–S6. Viết plan này, chờ Q1–Q6 |
| 2026-10-31 | Q1–Q6 đã chốt (mục 6). Tạo nhánh `feat/e03-schedule` từ `main`. Baseline API: 130 passed, 1 skipped, coverage 89,39% |
| 2026-10-31 | TDD: quy tắc thuần (15 test), 16 test tích hợp đỏ (ModuleNotFound, 404) → model, migration `c4e1a7d2f9b3`, service, router, schema. Round-trip upgrade/downgrade/upgrade sạch, `alembic check` không drift |
| 2026-10-31 | Seed M1/M8/M9 SGD-HCM: test đỏ 2 → xanh. Lint và format sạch. Kết quả: 172 passed, 1 skipped, coverage 87,10% |

## 11. Trạng thái cuối phiên (2026-10-31)

Trạng thái ở mục 7 là lúc lập plan. Bảng dưới đây là trạng thái thực tế.

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Pha 0 | ✅ | Baseline xanh trên PostgreSQL 16 của container `pmis-e1-test` (cổng 5433) |
| Pha 1 (bảng và migration) | ✅ | `milestones_wbs`, `hold_points`, `hold_point_confirmations`, `milestone_adjustments`, `penalty_rules`, `project_risks_and_issues` (migration `e8b2c5f1a3d4`) |
| Pha 2 (quy tắc thuần) | ✅ | `app/core/schedule_rules.py`, 15 unit test |
| Pha 3 (service) | ✅ | Mốc, điểm dừng, phạt, CR/NCR/rủi ro (`app/services/risk_issues.py`) |
| Pha 4 (router) | ✅ | `/milestones`, `/hold-points`, `/penalty-rules`, `/milestones/{id}/penalty`, `/risk-issues` |
| Pha 5 (seed) | 🟡 | Chỉ M1, M8, M9. M2–M7 chưa có ngày trong spec (xem S7) |
| Pha 6 (kiểm chứng) | 🟡 | Lint, format, `alembic check`, 172 test xanh. Chưa rà soát bảo mật bằng agent `security-reviewer` |
| Commit, push | ⏸ | Chỉ khi người dùng yêu cầu |

**Lệch so với plan ban đầu (đã quyết định trong lúc làm):**
- `milestones_wbs` bỏ hai cột `hold_point_code` và `checklist_code`. Liên kết H nằm ở `hold_points.milestone_id`, tránh lưu hai nguồn.
- Thêm bảng `penalty_rules` và `milestone_adjustments` theo G3 và G4. Phạt tính theo hợp đồng do người gọi chỉ định (`contract_id`), vì spec không cho mốc biết hợp đồng nào.
- Mốc khóa = mốc đã `COMPLETED` hoặc mốc cứng. Đổi `adjusted_end` của mốc khóa bắt buộc có lý do và tạo bản ghi điều chỉnh.
- `AT_RISK` được suy ra khi `adjusted_end` lớn hơn `baseline_end`. Đây là định nghĩa của tôi, spec không nói rõ. Cần người dùng xác nhận.
- `penalty_amount` cộng dồn theo số ngày trễ của mốc, không theo từng phần việc.

**Mã CR/NCR (Q4, đã chốt):** `{mã dự án}-{LOẠI}-{SỐ 3 chữ số}`, LOẠI theo `record_type` (RISK, ISSUE, CR, NCR, CONTRACT_DISCREPANCY). VD `SGD-HCM-CSVC-2026-NCR-001`. Mã này khác ví dụ `CRY-SGD-NCR-001` trong spec, theo quyết định lấy tiền tố từ mã dự án.

**Chưa làm và lý do:**
- **Đường găng:** ⏸ theo Q2.
- **M2–M7 SGD-HCM:** spec không ghi ngày. Không điền từ trí nhớ.
- **Seed Lâm Đồng (DOT_1–DOT_3):** chờ dữ liệu, cùng hướng B1 của E2.
- **Điểm dừng H0–H9 đã seed:** chưa seed, vì spec không ghi tên từng điểm dừng.

**Mâu thuẫn trong spec (S7, mới):** §4 nói M1 "chậm 16 ngày", nhưng điều chỉnh 07/10 → 05/11 là 29 ngày. Seed dùng ngày trong spec (07/10 và 05/11), tên mốc M1 để trống để xác nhận.

**Việc bạn cần làm:**
1. Cho biết `PREFIX` và `LOẠI` của CR/NCR theo dự án.
2. Xác nhận định nghĩa `AT_RISK` và ngày gốc của M1 (07/10 hay ngày khác, vì mâu thuẫn S7).
3. Cung cấp ngày M2–M7 và tên M1 nếu có.
