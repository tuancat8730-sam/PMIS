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
| E1 | Danh mục đa dự án, template archetype, bên liên quan, nhân sự chủ chốt, hợp đồng | P1, §4 | E0 | M | 1 | Chưa làm |
| E2 | Đơn vị thụ hưởng, tên kép sau sáp nhập, cụm địa lý | P2 | E0, E1 | S | 1 | Chưa làm |
| E3 | Tiến độ: baseline kép, đường găng, slippage, phạt, H0–H9, CR/NCR, rủi ro | P4 | E1, E2 | L | 2 | Chưa làm |
| E4 | Checklist pháp lý 89+ hồ sơ, máy trạng thái trưởng thành (chưa có Drive) | P3.1–3.2 | E1 | M | 2 | Chưa làm |
| E5 | Google Drive 2 chiều | P3.3 | E4 | L | 2 | Chưa làm |
| E6 | AI Auditor: kiểm chữ ký/dấu, rà soát lỗi pháp lý | P3.4 | E4, E5 | L | 4 | Chưa làm |
| E7 | Tài chính: đa hợp đồng, bảo lãnh, tạm ứng, giải ngân | P7 | E1 | M | 2 | Chưa làm |
| E8 | Module CNTT: khảo sát, RTM, mâu thuẫn hợp đồng, phân hệ A–G, NFR, ATTT | P5 | E1, E3 | L | 3 | Chưa làm |
| E9 | Module thiết bị: hàng mẫu 21 tiêu chí, serial/IMEI, CO/CQ, ma trận 62×4×3, 240+ biên bản `.docx` | P6 | E1, E2 | XL | 3 | Chưa làm |
| E10 | Mobile PWA hiện trường: quét QR/serial, ảnh có GPS, ký BB | §5.5 | E9 | M | 3 | Chưa làm |
| E11 | Auto-Report Studio: báo cáo tuần, meeting note, AI bóc tách biên bản họp | P8 | E3, E4, E9 | L | 4 | Chưa làm |
| E12 | Command Center: KPI, thẻ cảnh báo đỏ, đếm ngược hợp đồng | P1.1 | E1–E9 | M | 2 (cơ bản) → 4 | Chưa làm |

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
