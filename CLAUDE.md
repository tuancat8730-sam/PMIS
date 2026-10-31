# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

PMIS là hệ thống quản trị đầu tư công. Nguồn sự thật về phạm vi là `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` (tiếng Việt). Kế hoạch theo epic và trạng thái từng epic nằm ở `.claude/plans/pmis-epics.plan.md`; hiện chỉ E0 (nền tảng) có code. Khi làm một epic, đọc đúng phần tương ứng trong spec và cập nhật plan.

Thứ tự triển khai đã chốt là lát cắt cấp tốc: E0 → E2 → E9 → E11, rồi các epic còn lại.

## Commands

Chạy từ gốc repo (Makefile) trừ khi ghi khác.

### Backend (`apps/api`, Python 3.12)

```bash
make api-install                         # tạo .venv và pip install -e ".[dev]"
make api-test                            # pytest --cov (cần TEST_DATABASE_URL, xem dưới)
make api-lint                            # ruff check + ruff format --check
make api-migrate                         # alembic upgrade head
make create-admin EMAIL=... NAME="..."   # tạo ADMIN đầu tiên (hỏi mật khẩu)
```

Chạy một test cụ thể (từ `apps/api`):

```bash
./.venv/bin/pytest tests/unit/test_security.py::test_expired_access_token_is_rejected
./.venv/bin/pytest tests/integration/test_auth_api.py -k wrong_password
```

Integration test cần PostgreSQL thật. Đặt `TEST_DATABASE_URL` trỏ tới database có hậu tố `_test`, ví dụ `postgresql+asyncpg://pmis:pmis@localhost:5432/pmis_test`. Fixture **xóa toàn bộ schema `public`** rồi chạy migration từ đầu, nên không được trỏ vào database có dữ liệu thật. Không đặt biến thì các test integration bị skip, không fail.

Chạy API cục bộ: `./.venv/bin/uvicorn app.main:create_app --factory --reload`. Cần `DATABASE_URL`, `JWT_SECRET` (≥32 ký tự), `CCCD_ENCRYPTION_KEY` (xem `.env.example`). Thiếu biến nào, `Settings` báo lỗi ngay khi khởi động.

Ngưỡng coverage 80% nằm ở `[tool.coverage.report] fail_under` trong `pyproject.toml`; chỉ được kiểm tra khi chạy với `--cov`.

### Frontend (`apps/web`, Next.js 15 + React 19 + Tailwind v4)

```bash
make web-install                         # pnpm install
make web-lint                            # pnpm lint (eslint)
make web-test                            # pnpm test (vitest run)
make web-build                           # pnpm build (turbopack)
cd apps/web && pnpm vitest run src/lib/api.test.ts -t "returns ok"   # một test
cd apps/web && pnpm dev                  # dev server cổng 3000
```

Frontend đọc URL API từ `NEXT_PUBLIC_API_URL` (mặc định `http://localhost:8000`).

### Toàn stack

`make up` / `make down` chạy `docker compose` (Postgres 16, Redis 7, api, web). Compose đọc `.env` ở gốc nên phải tạo `.env` từ `.env.example` trước. Chưa kiểm chứng `docker compose up` end-to-end trên máy phát triển hiện tại.

## Architecture

### Monorepo

Hai ứng dụng độc lập, không có package dùng chung:
- `apps/api`: FastAPI backend, toàn bộ logic nghiệp vụ.
- `apps/web`: Next.js frontend. Hiện chỉ có trang trạng thái API.

CI (`.github/workflows/ci.yml`) chạy hai job `api` và `web` độc lập.

### Backend: layering

Luồng bắt buộc khi thêm endpoint: **router → service → model**.

- `app/main.py` có factory `create_app(settings)`. Hạ tầng được gắn vào `app.state` (`settings`, `engine`, `session_factory`). Không có object toàn cục; test tạo app riêng với `Settings` riêng.
- `app/api/deps.py` cung cấp `SessionDep` và `SettingsDep` (Annotated `Depends`). Router lấy session và settings qua hai alias này.
- `app/api/v1/` là router mỏng, gom trong `app/api/v1/__init__.py` với prefix `/api/v1`.
- `app/services/` chứa nghiệp vụ và truy vấn. **Service không commit**. Router quyết định `session.commit()` để thao tác nghiệp vụ và dòng audit nằm trong cùng một transaction.
- `app/models/` dùng SQLAlchemy 2.0 (`Mapped`), kế thừa `app/db/base.py::Base` (có naming convention cho constraint). Model phải được import trong `app/models/__init__.py` để Alembic thấy đủ bảng.
- `app/schemas/` dùng Pydantic v2. Request kế thừa `RequestModel` (`extra="forbid"`). Response không bao giờ chứa `hashed_password`.

### Auth và phân quyền

- Đăng nhập bằng `OAuth2PasswordRequestForm` (`username` là email) tại `/api/v1/auth/login`, trả JWT có claims `sub` (user id) và `role`.
- Xác thực **stateless**: `get_current_principal` (`app/core/rbac.py`) chỉ giải mã JWT, không tra DB. Hệ quả: đổi vai trò hoặc khóa tài khoản chỉ có hiệu lực khi token hết hạn. Riêng `/auth/me` có kiểm tra `is_active` trong DB.
- Phân quyền theo vai trò toàn cục qua `require_roles(Role.X, ...)`. Phân quyền theo dự án (theo spec) chưa có, sẽ thêm ở E1.
- `TOKEN_ISSUER` và `TOKEN_AUDIENCE` nằm trong `app/core/security.py`; token của issuer khác bị từ chối.
- Khi email không tồn tại, `services/auth.py` vẫn chạy một lần băm giả để thời gian phản hồi không lộ danh tính.

### Audit log

Thao tác ghi quan trọng gọi `services/audit.py::record_audit(...)` trong cùng session. `actor_id` là `None` cho đăng nhập thất bại và thao tác bootstrap. Dòng trong `audit_logs` không được cập nhật hay xóa.

### Mã hóa trường nhạy cảm

`app/core/crypto.py::FieldCipher` (Fernet) dành cho CCCD, khóa lấy từ `CCCD_ENCRYPTION_KEY`. Chưa có model nào dùng; E1 sẽ là nơi đầu tiên áp dụng.

### Migration

- `alembic.ini` không chứa URL. `migrations/env.py` lấy URL theo thứ tự: `config.attributes["database_url"]` (test truyền vào), rồi `Settings.database_url`.
- Env chạy bất đồng bộ (`async_engine_from_config`, `NullPool`).
- Migration đầu tiên được sinh bằng autogenerate và đã sửa tay phần `downgrade` (thêm `DROP TYPE` cho enum `user_role`). Autogenerate không tự xóa enum, nên luôn kiểm tra `downgrade` sau khi sinh.
- Khi thêm model: tạo migration mới, rồi kiểm tra `make api-migrate` và `alembic check` đều sạch.

### Test

- `tests/unit/` không cần DB; test RBAC dùng `httpx.ASGITransport`.
- `tests/integration/` dựng schema bằng **Alembic** (fixture `migrated_database`), không dùng `create_all`, nên migration luôn được kiểm chứng.
- `helpers.py` chứa `login_as` và `TEST_PASSWORD`; `conftest.py` chứa fixture. Fixture autouse `clean_tables` `TRUNCATE` `users` và `audit_logs` trước mỗi test.
- Marker `unit` và `integration` khai báo trong `pyproject.toml`; mỗi file đặt `pytestmark`.

### Frontend

- `src/lib/api.ts` là điểm duy nhất gọi API. `fetchApiHealth` nhận `fetchImpl` để test không cần mạng.
- `src/app/page.tsx` là Server Component `async`, gọi API với `cache: "no-store"`.

## Conventions

- Chuỗi hiển thị cho người dùng, thông điệp lỗi API, comment và docstring đều viết **tiếng Việt có dấu** (ví dụ `"Email hoặc mật khẩu không đúng"`). Tên biến, hàm và tên test dùng tiếng Anh.
- Hàm Python có type annotation đầy đủ. Ruff bỏ qua S105/S106 (tên hằng như `TOKEN_ISSUER` không phải mật khẩu) và nới B008 cho `Depends`/`Security`; cấu hình nằm trong `[tool.ruff]`.

## Quy ước chung (ECC, áp dụng cho mọi project)

**Code**
- Không sửa tại chỗ dữ liệu đầu vào: trả về bản mới. Ngoại lệ: ORM object trong service/test đã được session quản lý.
- KISS, DRY, YAGNI: không tạo abstraction khi mới có một chỗ dùng.
- Hàm dưới 50 dòng; file dưới 800 dòng (ngưỡng mềm); tránh lồng quá 4 cấp, dùng early return.
- Xử lý lỗi tường minh ở mọi tầng; không nuốt lỗi. Thông báo cho người dùng dễ hiểu, log chi tiết phía server.
- Validate tại mọi biên: input API, file, dữ liệu từ hệ thống ngoài. Python dùng schema Pydantic; frontend dùng Zod khi có form.
- Không hard-code bí mật hay magic number; đặt hằng số có tên.
- Python: PEP 8, `@dataclass(frozen=True)` cho DTO (ví dụ `Principal`). Không `print()` trong code production; dùng `logging`.
- TypeScript: kiểu tường minh cho hàm export, không dùng `any` (dùng `unknown` rồi thu hẹp), props là `interface` đặt tên, không dùng `React.FC`, không `console.log` trong production.
- Không đưa nội dung HTML chưa được làm sạch vào DOM (`dangerouslySetInnerHTML`, `innerHTML`).

**Kiểm thử**
- TDD bắt buộc: viết test trước, chạy thấy đỏ, viết code tối thiểu để xanh, rồi refactor. Độ phủ tối thiểu 80%.
- Test theo AAA (`# Arrange`, `# Act`, `# Assert`), tên mô tả hành vi.

**Review và bảo mật**
- Sau khi viết hoặc sửa code: tự review trước khi báo xong.
- Bắt buộc xem xét bảo mật khi đụng đến auth, input người dùng, truy vấn DB, thao tác file, gọi API ngoài, mã hóa, hoặc tài chính/thanh toán. Hiện các mục này có trong E0 (auth, mã hóa CCCD) và E1 trở đi.
- Mọi endpoint đăng nhập và endpoint ghi phải có rate limit. Chưa làm cho login (xem `.claude/plans/pmis-epics.plan.md`, E0).
- Không commit secret; `.env` đã nằm trong `.gitignore`.

**Commit (chỉ khi có yêu cầu)**
- Định dạng `<type>: <mô tả>` với type thuộc `feat | fix | refactor | docs | test | chore | perf | ci`.
- Không thêm `Co-Authored-By` (ECC mặc định tắt trong settings máy).

## Quy ước từ PXVB áp dụng cho PMIS

Các rule dưới đây lấy từ CLAUDE.md của PXVB, đã đổi cho phù hợp stack và quy trình của PMIS.

**Nghiệp vụ và dữ liệu**
- Spec `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` là nguồn sự thật. Khi spec mơ hồ hoặc có số liệu mâu thuẫn, ghi vào mục rủi ro/quyết định của plan thay vì tự chọn lặng lẽ.
- Ngưỡng, tỷ lệ phạt, định mức, giờ và danh mục không hard-code trong logic; lưu trong cấu hình hoặc bảng có phiên bản.
- Thời gian lưu UTC (`timestamptz`). Giá trị enum lưu dạng chuỗi UPPER_SNAKE.
- Dữ liệu đã khóa (ví dụ hồ sơ đã `VERIFIED_CLOSED`, biên bản đã ký) không sửa trực tiếp; thay đổi đi qua một bản ghi điều chỉnh có audit.
- Mọi thao tác ghi quan trọng phải ghi audit trong cùng transaction.

**Giao diện**
- UI 100% tiếng Việt, định dạng ngày và số theo vi-VN.
- Giao diện hiện trường (E10, tablet/PWA): nút chạm tối thiểu 56 dp; thao tác đạt/không đạt tối đa 3 lần chạm.

**Thiết bị hiện trường (áp dụng khi làm E10 hoặc bất kỳ lệnh ghi nào từ thiết bị)**
- Mỗi lệnh ghi gửi kèm `Idempotency-Key` và `X-Device-Id`.
- Xung đột đồng bộ không ghi đè dữ liệu của nhau; trả về xung đột để người dùng quyết định.

**Quy trình theo epic**
- Mỗi epic làm trên nhánh riêng `feat/e<nn>-<slug>` (ví dụ `feat/e02-identity`), tạo từ `main` mới nhất. Không commit trực tiếp lên `main`.
- Khi xong một task: plan được cập nhật (trạng thái, kết quả kiểm chứng, nhật ký) trong cùng thay đổi; test liên quan phải xanh trước khi đánh dấu xong.
- Add file theo tên cụ thể, không dùng `git add -A`. Kiểm tra `git diff --cached` trước khi commit: không có secret, không có `.venv/`, `node_modules/`, `.DS_Store`.
- Đồng bộ với `main` bằng merge, không rebase sau khi đã push. Không `--no-verify`, không force-push trừ khi được yêu cầu rõ.
- Không tự merge PR.
- Trước khi báo một task là xong: test và lint xanh, quyền và audit đã áp dụng, mục tiêu của task đạt, OpenAPI đã cập nhật (FastAPI tự sinh tại `/openapi.json`).

**Không áp dụng cho PMIS** (stack khác): Java/Spring/ArchUnit/Maven/Flyway; MySQL và Testcontainers; Docker Colima; cấu trúc module `domain/application/infrastructure/api/contract`; UUIDv7 (xem xung đột); hệ thiết kế `docs/DESIGN-SYSTEM.md` và quy trình sinh màn hình của PXVB; luồng duyệt/ký của PXVB.

## Xung đột cần quyết định

| Chủ đề | PXVB / ECC | PMIS hiện tại | Đề xuất |
|---|---|---|---|
| Commit và push | PXVB: commit và push ngay sau mỗi task | Hệ thống chỉ commit khi người dùng yêu cầu | Giữ mặc định không commit; chỉ commit khi có yêu cầu |
| Khóa chính | PXVB: UUIDv7 | Spec §4 và migration dùng `gen_random_uuid()` (v4) | Giữ v4 theo spec; đổi cần quyết định trước E1 |
| Định dạng response | ECC: envelope `success / data / error / meta` | FastAPI trả `detail` (mặc định) | Quyết định trước E1 để áp đồng nhất |
| Nơi lưu plan | PXVB: `docs/plans/E<nn>-*.plan.md` | `.claude/plans/pmis-epics.plan.md` | Giữ `.claude/plans/` |
| Co-Authored-By | PXVB: thêm nếu cấu hình cho phép | ECC mặc định tắt | Không thêm |
