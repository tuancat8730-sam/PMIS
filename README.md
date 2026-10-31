# PMIS — Hệ thống quản trị và giám sát dự án đầu tư công

Monorepo gồm hai ứng dụng độc lập:

- `apps/api`: backend FastAPI (Python 3.12, SQLAlchemy async, PostgreSQL 16, Alembic).
- `apps/web`: frontend Next.js 15 (React 19, Tailwind v4). Hiện chỉ có trang trạng thái API.

Nguồn sự thật về phạm vi là `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md`. Kế hoạch theo epic nằm ở `.claude/plans/`.

## Yêu cầu

- Docker (hoặc Docker Desktop / Colima) cho PostgreSQL và chạy toàn bộ stack.
- Python 3.12 và `make` nếu chạy API cục bộ.
- Node.js 22 và pnpm 9 nếu chạy web cục bộ.

## Cấu hình

Sao chép file mẫu rồi điền giá trị thật. Không commit file `.env`.

```bash
cp .env.example .env
```

| Biến | Bắt buộc | Ghi chú |
|---|---|---|
| `POSTGRES_PASSWORD` | Có (dùng cho compose) | Mật khẩu PostgreSQL trong container |
| `JWT_SECRET` | Có | Tối thiểu 32 ký tự. Tạo bằng `openssl rand -hex 32` |
| `CCCD_ENCRYPTION_KEY` | Có | Khóa Fernet, tạo bằng lệnh trong `.env.example` |
| `DATABASE_URL` | Không | Chỉ dùng khi chạy API ngoài compose |
| `CORS_ORIGINS` | Không | Danh sách origin của frontend, định dạng JSON |
| `LOGIN_RATE_LIMIT_ATTEMPTS` / `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Không | Mặc định 5 lần / 900 giây, tính theo IP |
| `WRITE_RATE_LIMIT_ATTEMPTS` / `WRITE_RATE_LIMIT_WINDOW_SECONDS` | Không | Mặc định 30 lần / 60 giây, tính theo IP, áp cho endpoint ghi |

Thiếu `JWT_SECRET` hoặc `CCCD_ENCRYPTION_KEY`, API báo lỗi ngay khi khởi động.

## Chạy toàn bộ stack bằng Docker

```bash
make up        # docker compose up --build
make down      # docker compose down
```

Sau khi chạy:

- API: http://localhost:8000 (tài liệu OpenAPI tại `/docs`)
- Web: http://localhost:3000

Lần đầu, tạo tài khoản ADMIN bên trong container `api` (lệnh hỏi mật khẩu, tối thiểu 12 ký tự):

```bash
docker compose exec api python -m app.cli create-admin --email admin@example.com --name "Quản trị viên"
```

Khi chạy cục bộ không dùng Docker, dùng `make create-admin EMAIL=... NAME="..."`.

## Chạy cục bộ không dùng Docker cho API

```bash
make api-install                       # tạo .venv và cài dependency
make api-migrate                       # alembic upgrade head
cd apps/api && ./.venv/bin/uvicorn app.main:create_app --factory --reload
```

Cần `DATABASE_URL` trỏ tới PostgreSQL đang chạy.

## Chạy cục bộ cho web

```bash
make web-install
cd apps/web && pnpm dev                # cổng 3000
```

Frontend đọc URL API từ `NEXT_PUBLIC_API_URL` (mặc định `http://localhost:8000`).

## Kiểm thử và lint

Integration test cần PostgreSQL thật. Fixture xóa toàn bộ schema `public`, nên `TEST_DATABASE_URL` phải trỏ tới database có hậu tố `_test`. Không đặt biến này thì các test integration bị bỏ qua, không báo lỗi.

```bash
# API
make api-lint
TEST_DATABASE_URL=postgresql+asyncpg://pmis:pmis@localhost:5432/pmis_test make api-test

# Web
make web-lint
make web-test
make web-build
```

Ngưỡng coverage 80% nằm trong `apps/api/pyproject.toml` và chỉ được kiểm khi chạy với `--cov`.

## Cấu trúc thư mục

```text
apps/api/        Backend FastAPI (router -> service -> model)
apps/web/        Frontend Next.js
.claude/plans/   Kế hoạch theo epic và kế hoạch hoàn thành E0
docker-compose.yml, Makefile, .env.example
```

## Lưu ý vận hành

- Giới hạn tần suất lưu trong bộ nhớ của từng tiến trình API. Khi chạy nhiều worker hoặc nhiều replica, mỗi tiến trình đếm riêng. Cần chuyển sang Redis trước khi scale ngang.
- Giới hạn tần suất lấy địa chỉ từ kết nối TCP, không đọc `X-Forwarded-For`. Khi đặt sau reverse proxy, phải cấu hình proxy đáng tin cậy trước.
