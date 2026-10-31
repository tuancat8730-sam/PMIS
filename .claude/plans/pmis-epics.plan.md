# Plan: Hoàn thành PMIS (Hệ thống quản trị & giám sát dự án đầu tư công)

**Source**: `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md`
**Repo**: `git@github.com:tuancat8730-sam/PMIS.git` (chưa commit)
**Cập nhật**: 2026-10-31
**Complexity**: Large (13 epic, chia theo lát cắt cấp tốc)

## Quyết định đã chốt

| Hạng mục | Lựa chọn | Ghi chú |
|---|---|---|
| Thứ tự triển khai | Lát cắt cấp tốc: E0 → E2 → E9 → E11, sau đó các epic còn lại | Đợt 1 Lâm Đồng đã bắt đầu 27/10; M8 cố định 30/11 |
| Job queue (worker nền) | ARQ | Dùng cho Drive sync, OCR, xuất hàng loạt biên bản |
| LLM (AI Auditor, bóc tách biên bản) | Google Gemini qua `google-genai` | Không gửi CCCD/PII sang LLM |
| Git | Repo `PMIS` trên GitHub, `origin` đã trỏ | Chưa commit; commit khi người dùng yêu cầu |

## Epic

| Epic | Tên | Phân hệ spec | Phụ thuộc | Độ lớn | Phase | Trạng thái |
|---|---|---|---|---|---|---|
| E0 | Nền tảng: monorepo, DB, auth/RBAC, audit log, CI | §2, §6 | — | M | 1 | **Đã làm phần lớn** (xem bên dưới) |
| E1 | Danh mục đa dự án, template archetype, bên liên quan, nhân sự chủ chốt, hợp đồng | P1, §4 | E0 | M | 1 | **Đã làm** (chưa commit; xem `e01-portfolio.plan.md`) |
| E2 | Đơn vị thụ hưởng, tên kép sau sáp nhập, cụm địa lý | P2 | E0, E1 | S | 1 | **Đang làm** trên `feat/e02-beneficiary` (API và seed TP.HCM xong, 130 test xanh; chờ B1 để seed 62 đơn vị Lâm Đồng; xem `e02-beneficiary.plan.md`) |
| E3 | Tiến độ: baseline kép, đường găng, slippage, phạt, H0–H9, CR/NCR, rủi ro | P4 | E1, E2 | L | 2 | **Đang làm** trên `feat/e03-schedule`: mốc, H0–H9, phạt, seed M1/M8/M9 xong; CR/NCR/rủi ro và đường găng còn lại (xem `e03-schedule.plan.md`) |
| E4 | Checklist pháp lý 89+ hồ sơ, máy trạng thái trưởng thành (chưa có Drive) | P3.1–3.2 | E1 | M | 2 | **Đã làm phần lớn** trên `feat/e04-legal` (máy trạng thái, bảng, API, 219 test xanh). Seed 89+ đầu mục chờ file Excel từ PM (Q1). Plan: `e04-legal.plan.md` |
| E5 | Google Drive 2 chiều | P3.3 | E4 | L | 2 | Chưa làm. Plan: `e05-drive.plan.md` (chờ Q1–Q4) |
| E6 | AI Auditor: kiểm chữ ký/dấu, rà soát lỗi pháp lý | P3.4 | E4, E5 | L | 4 | Chưa làm. Plan: `e06-ai-auditor.plan.md` (chờ Q1–Q5) |
| E7 | Tài chính: đa hợp đồng, bảo lãnh, tạm ứng, giải ngân | P7 | E1 | M | 2 | Chưa làm. Plan: `e07-finance.plan.md` (chờ Q1–Q4) |
| E8 | Module CNTT: khảo sát, RTM, mâu thuẫn hợp đồng, phân hệ A–G, NFR, ATTT | P5 | E1, E3 | L | 3 | Chưa làm. Plan: `e08-it-system.plan.md` (chờ Q1–Q7) |
| E9 | Module thiết bị: hàng mẫu 21 tiêu chí, serial/IMEI, CO/CQ, ma trận 62×4×3, 240+ biên bản `.docx` | P6 | E1, E2 | XL | 3 | Chưa làm. Plan: `e09-goods.plan.md` (chờ Q1–Q5; đợt D chờ file mẫu) |
| E10 | Mobile PWA hiện trường: quét QR/serial, ảnh có GPS, ký BB | §5.5 | E9 | M | 3 | Chưa làm. Plan: `e10-field-pwa.plan.md` (chờ Q1–Q6) |
| E11 | Auto-Report Studio: báo cáo tuần, meeting note, AI bóc tách biên bản họp | P8 | E3, E4, E9 | L | 4 | Chưa làm. Plan: `e11-reports.plan.md` (chờ Q1–Q5) |
| E12 | Command Center: KPI, thẻ cảnh báo đỏ, đếm ngược hợp đồng | P1.1 | E1–E9 | M | 2 (cơ bản) → 4 | Chưa làm. Plan: `e12-command-center.plan.md` (chờ Q1–Q5) |

Các câu hỏi cần chốt trước khi bắt đầu, tổng hợp từ 9 plan trên:
- **Lệch lát cắt cấp tốc:** E11 đứng sau E9 nhưng cần E4. Đề xuất đưa E4 lên trước E11 (`e11-reports.plan.md` Q4).
- **Số liệu:** tổng giá trị hợp đồng (111,8 tỷ trong spec; 111,07 tỷ chỉ gói chính; 112,19 tỷ kể cả tư vấn) và số trường (1.670 hay 1.732). Ảnh hưởng E2, E8, E9, E12.
- **Số đơn vị đợt 1:** spec ghi 60, ma trận ghi 62 (`e09-goods.plan.md` Q3).
- **Thiếu file mẫu:** biên bản bàn giao (E9), báo cáo tuần và meeting note (E11), danh mục 89 đầu mục (E4).

## Thứ tự thực thi

1. **Cấp tốc:** E0 → E2 → E9 → E11
2. **Phase 2:** E1, E3, E4, E5, E7, E12 (bản cơ bản)
3. **Phase 3:** E8, E10
4. **Phase 4:** E6, phần AI của E11, E12 hoàn chỉnh

## E0 — Trạng thái chi tiết

### Đã làm
- **Backend `apps/api`:** FastAPI, SQLAlchemy 2.0 async, Alembic, pyproject, cấu hình fail-fast khi thiếu secret.
- **Auth:** JWT HS256 có issuer/audience/exp; băm mật khẩu Argon2 (`pwdlib`); endpoint `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- **RBAC:** 7 vai trò (ADMIN, PM, PM_CONSULTANT, SUPERVISION_CONSULTANT, INVESTOR, CONTRACTOR, FIELD_ENGINEER); dependency `require_roles(...)`.
- **Người dùng:** `POST /api/v1/users` (chỉ ADMIN), trùng email trả 409, mật khẩu tối thiểu 12 ký tự, schema từ chối trường lạ.
- **Audit log:** ghi `auth.login`, `auth.login_failed`, `user.create`, `user.create_admin_bootstrap`.
- **Mã hóa CCCD:** `FieldCipher` (Fernet). Chưa gắn vào model.
- **Migration:** `b9561eaced0e` tạo `users`, `audit_logs`, enum `user_role`. Đã kiểm tra downgrade/upgrade và `alembic check` không drift.
- **CLI:** `python -m app.cli create-admin` (qua `make create-admin`).
- **Test:** 31 pass (15 unit, 16 integration trên PostgreSQL nhúng). Ruff sạch. Coverage tổng 82,95%.
- **Frontend `apps/web`:** Next.js 15.5, React 19, Tailwind v4, TypeScript, ESLint; `src/lib/api.ts` + 6 test Vitest; trang `/` hiển thị trạng thái API. Lint và build pass; trang `/` 113 kB JS.
- **Hạ tầng:** `docker-compose.yml`, `apps/api/Dockerfile`, `Makefile`, `.env.example`, `.gitignore`, `.github/workflows/ci.yml`.
- **Smoke test:** uvicorn chạy; health `ok`; đăng nhập sai đúng thông điệp; OpenAPI 200.

### Chưa làm / còn thiếu so với DoD
- [x] `docker compose up` đã kiểm chứng (docker-compose 5.6.1 qua Homebrew): db healthy, migration chạy, health 200, login sai 401, web 200
- [ ] CI chưa chạy (chưa push)
- [x] Rate limit cho `POST /api/v1/auth/login` và `POST /api/v1/users` (5/900s và 30/60s theo IP, trả 429 + `Retry-After`)
- [x] README hướng dẫn chạy (`README.md` ở gốc)
- [x] Test cho `main()` của CLI (`getpass`): unit và integration
- [x] Dockerfile cho `apps/web` (compose trỏ tới nhưng trước đây thiếu)
- [ ] Số liệu coverage theo từng file không khớp hành vi (`auth.py`); chưa tìm ra nguyên nhân, tổng 85,71% đạt ngưỡng
- [ ] Commit E0 lên `origin` (chờ xác nhận)

Kết quả kiểm chứng (2026-10-31): API 43/43 test xanh trên PostgreSQL 16, ruff sạch, alembic không drift; web lint, 6 test và build xanh. Chi tiết và nhật ký: `.claude/plans/e00-completion.plan.md`.

## E1 — Trạng thái chi tiết

### Đã làm
- **Bảng:** `projects` (archetype, health, tổng mức đầu tư `NUMERIC(18,2)`), `project_stakeholders` (kiểm tổng liên danh ≤ 100%), `contracts`, `contract_personnel` (CCCD mã hóa Fernet, chỉ lưu 4 số cuối để hiển thị, quét trùng trong dự án).
- **API:** `POST/GET /api/v1/projects`, `GET /api/v1/projects/{id}`, `POST/GET /api/v1/projects/{id}/stakeholders`, `POST/GET /api/v1/projects/{id}/contracts`, `POST/GET /api/v1/contracts/{id}/personnel`. Mọi thao tác ghi có audit cùng transaction và rate limit.
- **Migration:** `6b19966287e0`. `downgrade` xóa 4 enum. Round-trip và `alembic check` sạch.
- **RBAC theo dự án:** bảng `project_members`, guard theo thành viên trong `deps.py`. ADMIN toàn cục vượt qua.
- **Test:** 110/110 xanh (67 test mới), coverage 89,89%. Ruff sạch.

### Chưa làm / hoãn (xem `e01-portfolio.plan.md` mục 5)
- [x] RBAC theo dự án (`project_members`): thành viên đọc, PM ghi; nhân sự chỉ PM hoặc ADMIN (D3).
- [ ] Template engine sinh M1–M9, H0–H9, CL-01..10, 89 hồ sơ: chờ E3, E4 (D5).
- [ ] Seed dữ liệu thật: chuyển sang E2.
- [ ] Chạy lại `docker compose up` với migration E1.
- [ ] Commit E1 (chờ xác nhận; nhánh theo quy định phải tạo từ `main`, xem D7).

## Rủi ro đang mở

| Rủi ro | Mức | Biện pháp |
|---|---|---|
| Deadline cấp tốc (Đợt 1 đang chạy, M8 30/11) | Cao | Đi theo lát cắt cấp tốc; seed dữ liệu thật từ E2 |
| CCCD và nhân sự là PII | Cao | Mã hóa cột (đã có `FieldCipher`), RBAC theo dự án, không gửi PII sang LLM |
| Nội dung pháp lý (89 hồ sơ, 21 tiêu chí, căn cứ NĐ 45/2026, 224/2026) chưa được kiểm chứng | Cao | PM domain xác nhận checklist và mẫu trước khi seed |
| Số trường mâu thuẫn trong spec: 1.670 (§1.1, §5.1) vs 1.732 (KPI strip §5.1) | Trung bình | Chốt số đúng trước khi seed E2 |
| Schema ERD có thực thể chưa có DDL (`HOLD_POINTS`, `WEEKLY_REPORTS`, `IT_SURVEY_RECORDS`, `SAMPLE_INSPECTIONS`, `DELIVERY_BATCH_ITEMS`, `PAYMENT_DISBURSEMENTS`) | Trung bình | Bổ sung DDL trong epic tương ứng |
| Google Drive 2 chiều (xung đột, webhook, quota) | Trung bình | Một chiều trước, hai chiều sau; idempotent theo `drive_file_id` |
| Cấu trúc `docx` 240+ biên bản giữ đúng thể thức | Trung bình | Test so sánh với mẫu; sinh theo batch qua ARQ |

## Bước tiếp theo

1. E0: chạy CI sau khi push (compose đã kiểm chứng).
2. Chờ xác nhận commit E0 lên `origin`.
3. Chốt số trường (1.670 hay 1.732) với người phụ trách dự án.
4. Bắt đầu E2 (đơn vị thụ hưởng, seed 62 đơn vị Lâm Đồng và 8 đơn vị khảo sát HCM).

## Acceptance

- [x] Plan đã ghi ra file
- [ ] E0 đạt đủ DoD (còn CI chưa chạy và commit chưa làm, xem trên)
- [ ] E2 hoàn thành và seed được dữ liệu thật
