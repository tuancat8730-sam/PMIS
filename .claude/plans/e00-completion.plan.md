# Kế hoạch: Hoàn tất E0 (nền tảng: rate limit, CLI, README, docker compose, kiểm chứng)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (mục E0 — Trạng thái chi tiết, "Chưa làm / còn thiếu so với DoD"); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` §2, §6, §8 (Phase 1); `CLAUDE.md` (Backend, Auth, Quy ước chung: rate limit cho đăng nhập và endpoint ghi, TDD, audit).
**Độ phức tạp:** Trung bình. **Cập nhật lần cuối:** 2026-10-31.
**Phương pháp:** rà soát tĩnh `apps/api`, `apps/web`, `docker-compose.yml` và đối chiếu DoD trong plan epic. Thực hiện theo TDD: test đỏ → xanh → refactor. Mọi số liệu dưới đây là kết quả chạy thật ngày 2026-10-31.
**Chú giải:** ✅ xong · 🟡 xong một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E0 hoàn tất"

| Nhóm | Nội dung | Thuộc E0? |
|---|---|---|
| Backend nền: FastAPI, SQLAlchemy async, Alembic, cấu hình fail-fast | `apps/api` | ✅ Có sẵn, không đổi |
| Auth JWT, băm Argon2, RBAC 7 vai trò, audit log | `services/auth.py`, `core/rbac.py`, `services/audit.py` | ✅ Có sẵn, không đổi |
| Rate limit đăng nhập và endpoint ghi (`POST /users`) | `core/rate_limit.py`, `api/deps.py`, `main.py`, `api/v1/auth.py`, `api/v1/users.py` | ✅ Pha 1–2 |
| Test CLI `create-admin` (kể cả `main()`) | `tests/unit/test_cli.py`, `tests/integration/test_cli_main.py` | ✅ Pha 3 |
| README hướng dẫn chạy | `README.md` (gốc repo) | ✅ Pha 4 |
| Docker: image api và web build và chạy | `apps/web/Dockerfile`, `apps/web/.dockerignore`, `docker-compose.yml` | 🟡 Image và container đã chạy thật. Lệnh `docker compose up` chưa chạy được vì máy không có `docker compose` (xem F6) |
| CI xanh trên GitHub | `.github/workflows/ci.yml` | ⏸ Cần push. Commit và push chỉ làm khi người dùng yêu cầu |
| Commit E0 lên `origin` | — | ⏸ Chờ xác nhận người dùng (CLAUDE.md: không commit nếu không được yêu cầu) |

**E0 được đánh ✅ khi:** các mục Pha 1–6 xong; kiểm chứng mã xanh; compose chạy được; plan epic được cập nhật. Riêng compose hiện là 🟡 (xem F6), và CI, commit là hai mục ⏸.

## 2. Đánh giá hiện trạng theo DoD

| Yêu cầu (DoD E0) | Trạng thái | Bằng chứng |
|---|---|---|
| Rate limit `POST /auth/login` | ✅ | 429 + `Retry-After` sau 5 lần/900 giây theo IP. IT `test_login_is_rejected_with_429...`; kiểm lại trong container thật |
| Rate limit endpoint ghi | ✅ | `POST /users`: 30 lần/60 giây. IT `test_user_creation_is_rejected_with_429...` |
| Test `main()` của CLI | ✅ | Unit: mật khẩu ngắn trả 1 mà không chạm DB. IT: tạo admin trả 0, email trùng trả 1. `cli.py` 96% (dòng còn lại là nhánh `__main__`) |
| README | ✅ | `README.md` ở gốc, hướng dẫn cấu hình, compose, cục bộ, test, tạo admin |
| `docker compose up` | 🟡 | Build image api và web thành công; chạy container api, web, db trên cùng network: health 200, login sai 401, web 200, rate limit 429. Compose file chưa được chạy (F6) |
| Auth, RBAC, audit | ✅ | 31 test có sẵn vẫn xanh trên PostgreSQL 16 |
| Frontend trạng thái API | ✅ | `pnpm lint` sạch, `pnpm test` 6/6, `pnpm build` thành công |
| Migration không drift | ✅ | `alembic check`: "No new upgrade operations detected", head `b9561eaced0e` |

## 3. Phát hiện từ rà soát và triển khai

| ID | Mức | Phát hiện | Xử lý |
|---|---|---|---|
| F1 | CAO | Docker CLI không tìm thấy socket mặc định. Colima chạy ở `~/.colima/default/docker.sock` | Đặt `DOCKER_HOST` khi chạy lệnh Docker. Không sửa cấu hình máy |
| F2 | CAO | `docker-compose.yml` build `./apps/web` nhưng không có Dockerfile | Đã thêm `apps/web/Dockerfile` (node 22, pnpm 9, build rồi `next start`) và `.dockerignore` |
| F3 | TB | `POST /auth/login` không có giới hạn tần suất | Đã thêm rate limit (Pha 1–2) |
| F4 | TB | `TEST_DATABASE_URL` không có sẵn, integration test bị bỏ qua | Đã chạy PostgreSQL 16 cho test ở cổng 5433 và đặt biến môi trường khi chạy |
| F5 | THẤP | Coverage theo file của `app/api/v1/auth.py` báo chưa phủ các dòng 31–61 dù các test login (401, audit, token) đều xanh. Test sai mật khẩu xác nhận 401 và bản ghi audit. Tổng coverage vẫn đạt | **Chưa tìm ra nguyên nhân** (đã thử cô lập test, cô lập module, đọc lại code). Ghi nhận, không sửa. Tổng 85,71% đạt ngưỡng 80% |
| F6 | ✅ đã xử lý | Máy không có `docker compose` | Đã cài docker-compose 5.6.1 qua Homebrew và chạy stack đầy đủ bằng `docker compose up` (mục 6.4) |
| F7 | TB | Cổng host `5432` (db) và `8000` (api) đang bị dịch vụ khác của máy giữ (`qlda-pg`, ssh tunnel, uvicorn của project `ql_capxa`) | Đã đưa cổng vào biến `POSTGRES_HOST_PORT` và `API_HOST_PORT` trong compose (mặc định vẫn 5432 và 8000). Không dừng dịch vụ của project khác |
| F8 | TB | `NEXT_PUBLIC_API_URL` đặt ở `environment` của compose chỉ có tác dụng lúc chạy, không đi vào bundle | Chuyển thành `build.args`. Đã kiểm: `localhost:8100` xuất hiện trong chunk server của image |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| Docker (colima) | Đang chạy, cần `DOCKER_HOST` | Đã dùng để test và build |
| `docker compose` | Chưa có trên máy | Chặn việc kiểm chứng compose đầy đủ (F6) |
| `.env` | Tạo cục bộ với secret ngẫu nhiên, nằm trong `.gitignore` | Không commit. Giá trị không được in ra log |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Rate limit lưu trong bộ nhớ tiến trình | Nhiều worker hoặc replica thì mỗi tiến trình đếm riêng. Chuyển sang Redis (đã có trong compose) trước khi scale ngang |
| G2 | Khóa rate limit là IP từ kết nối TCP, không đọc `X-Forwarded-For` | Khi có reverse proxy đáng tin cậy, đọc header đó |
| G3 | Đăng nhập 5 lần / 900 giây; endpoint ghi 30 lần / 60 giây; tính theo IP | Điều chỉnh qua biến môi trường `*_RATE_LIMIT_*` |
| G4 | Test tích hợp đặt ngưỡng 100.000 để không ảnh hưởng nhau; test rate limit tự dựng app với ngưỡng thấp | Nếu muốn test ngưỡng mặc định, reset bộ đếm trước mỗi test |
| G5 | Web chạy bằng `next start` sau khi build | Đổi sang `output: standalone` nếu cần image nhỏ hơn |
| G6 | Khi không có IP (`request.client` là None), mọi request chung khóa `unknown` | Chấp nhận ở E0; môi trường thật luôn có IP |

## 6. Quyết định (theo mặc định, người dùng yêu cầu thực hiện)

| # | Quyết định | Trạng thái |
|---|---|---|
| D1 | Rate limit in-memory, class `SlidingWindowRateLimiter`, không thêm dependency | ✅ |
| D2 | Limiter gắn vào `app.state` trong `create_app`, không dùng biến toàn cục | ✅ |
| D3 | Trả 429 với `Retry-After` và thông điệp tiếng Việt | ✅ |
| D4 | Dependency là `async def` để chạy trên event loop; bộ đếm không có khóa | ✅ |
| D5 | Không commit trong kế hoạch này | ✅ (CLAUDE.md) |
| D6 | Không cài `docker compose` thay người dùng; kiểm chứng bằng container riêng và ghi rõ phần chưa chạy | ✅ |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0 – Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Ghi plan này | ✅ | |
| 0.2 | PostgreSQL 16 cho test | ✅ | Cổng 5433 (F7), container `pmis-e0-test` đã dọn |
| 0.3 | Baseline | ✅ | Integration 31/31 xanh, coverage 82,95% (trước khi sửa) |

### Pha 1 – Bộ giới hạn tần suất (unit)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ `tests/unit/test_rate_limit.py` (6 test) | ✅ | Đỏ: `ModuleNotFoundError` |
| 1.2 | `app/core/rate_limit.py` | ✅ | 6/6 xanh. Thêm test cho nhánh sweep giữ khóa còn hạn (7/7) |

### Pha 2 – Gắn vào endpoint
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Settings `*_RATE_LIMIT_*` (gt=0) | ✅ | `core/config.py` |
| 2.2 | Test đỏ IT (login và POST /users) | ✅ | Đỏ đúng lý do: 401 và 201 thay vì 429 |
| 2.3 | Limiter trong `app.state`, dependency `LoginRateLimitDep`, `WriteRateLimitDep` | ✅ | 2/2 xanh |
| 2.4 | Ngưỡng cao trong fixture `settings` (G4) | ✅ | Test cũ không bị 429 |

### Pha 3 – Test CLI
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Unit: mật khẩu ngắn → 1 | ✅ | Xanh ngay: test mô tả hành vi có sẵn, không đỏ trước |
| 3.2 | IT: tạo admin → 0; email trùng → 1 | ✅ | Xanh ngay (cùng lý do) |

### Pha 4 – Tài liệu
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | `README.md` ở gốc | ✅ | Đã sửa một hướng dẫn sai: `make create-admin` không chạy được trong container, thay bằng `docker compose exec api python -m app.cli ...` |

### Pha 5 – Kiểm chứng mã
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | API: ruff check, ruff format, pytest --cov, alembic check | ✅ | Ruff sạch (45 file đã định dạng). 43/43 test xanh trên PostgreSQL 16, coverage 85,71% (≥ 80%). Alembic không drift |
| 5.2 | Web: lint, test, build | ✅ | Lint sạch, 6/6 test, build thành công |
| 5.3 | Tự review diff: không secret, không `.env`, không `print` mới | ✅ | Quét secret trong file đã sửa: không có. `.env` nằm trong `.gitignore` |

### Pha 6 – Docker
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | `apps/web/Dockerfile` và `.dockerignore` | ✅ | Build thành công |
| 6.2 | Build image api và web; chạy db, api, web trên network | ✅ | Migration chạy trong container api khi khởi động |
| 6.3 | Smoke test | ✅ | Health 200 `{"status":"ok"}`; login sai 401 với thông điệp tiếng Việt; web 200 và render section API; login sai lần thứ 6 trả 429, `Retry-After` 885 |
| 6.4 | `docker compose up` | ✅ | Đã cài compose 5.6.1 (Homebrew), chạy `docker compose up -d --build` với cổng mặc định: db healthy, migration áp dụng, health 200, login sai 401, web 200. Sau đó `docker compose down` (giữ volume `pgdata`) |

### Pha 7 – Đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 7.1 | Cập nhật `.claude/plans/pmis-epics.plan.md` | ✅ | Xem mục E0 trong plan epic |
| 7.2 | Đo coverage theo file | 🟡 | Đã đo, lệch vẫn còn (F5) |
| 7.3 | Dọn container smoke và test; không commit | ✅ | Còn lại `qlda-pg` là của project khác, để nguyên |

## 8. Trạng thái theo yêu cầu (đích cần đạt)

| Yêu cầu | Hiện tại | Đích E0 | Pha |
|---|---|---|---|
| Rate limit login | ✅ | ✅ | 1, 2 |
| Rate limit ghi | ✅ | ✅ | 2 |
| Test CLI `main()` | ✅ | ✅ | 3 |
| README | ✅ | ✅ | 4 |
| Docker image và container | ✅ | ✅ | 6 |
| `docker compose up` | 🟡 | ✅ | 6.4 (cần cài compose) |
| PostgreSQL 16 | ✅ | ✅ | 0, 5 |
| CI | ⏸ | ⏸ (cần push) | – |
| Commit | ⏸ | ⏸ (chờ xác nhận) | – |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| TB | Rate limit trong bộ nhớ không chia sẻ giữa worker và replica | G1: Redis trước khi scale ngang |
| TB | Sau reverse proxy, mọi người dùng có thể chung một khóa IP | G2: cấu hình proxy đáng tin trước khi bật production |
| TB | `docker compose up` chưa được chạy thật, có thể có lỗi chỉ lộ ra khi chạy compose | Cài compose và chạy `make up` trước khi đánh ✅ tuyệt đối (F6) |
| THẤP | Coverage theo file không khớp hành vi (F5) | Ghi nhận; tổng đạt ngưỡng |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Đọc template PXVB E08, plan E0 và code liên quan. Baseline: ruff sạch, 15 unit xanh. Phát hiện F1–F5. Viết plan này |
| 2026-10-31 | Pha 0: container test ở cổng 5433, vì 5432 bị `qlda-pg` và ssh tunnel giữ (F7). Baseline integration 31/31 xanh, coverage 82,95% |
| 2026-10-31 | Pha 1 (TDD): test đỏ `ModuleNotFoundError: app.core.rate_limit` → `SlidingWindowRateLimiter` 6/6 xanh. Thêm test nhánh sweep → 7/7 |
| 2026-10-31 | Pha 2 (TDD): IT đỏ (401 và 201 thay vì 429) → settings, limiter trong `app.state`, dependency login và ghi → 2/2 xanh. Ngưỡng cao trong conftest |
| 2026-10-31 | Pha 3: test CLI (unit và IT) xanh ngay vì mô tả hành vi có sẵn. Ghi nhận, không phải test đỏ |
| 2026-10-31 | Pha 4: README. Sửa một hướng dẫn sai về `make create-admin` trong container |
| 2026-10-31 | Pha 5: API 43/43 xanh, coverage 85,71%, ruff sạch, alembic không drift. Web lint, 6 test, build xanh |
| 2026-10-31 | Pha 6: thêm `apps/web/Dockerfile`, `.dockerignore`; compose đổi `build.args` và cổng biến đổi (F7, F8). Lần đầu build api lỗi `content digest not found`, pull lại base image rồi build được. Chạy db, api, web trên network: smoke test đạt. Không có `docker compose` nên compose chưa chạy (F6) |
| 2026-10-31 | F5 điều tra không ra nguyên nhân. Ghi nhận, chưa sửa |
| 2026-10-31 | Dọn container smoke và test. Chưa commit, chưa push. CI chưa chạy |
| 2026-10-31 | Theo yêu cầu người dùng: `docker stop qlda-pg` (giữ container và volume), kill uvicorn PID 26008 của `ql_capxa` (cổng 8000). Cài `docker-compose` qua Homebrew, đăng ký làm plugin trong `~/.docker/cli-plugins`. Chạy `docker compose up` với cổng mặc định: smoke đạt, sau đó `docker compose down` |
| 2026-10-31 | F6 đã giải quyết. Ssh tunnel PID 31772 từng giữ 5432 không nằm trong yêu cầu; sau khi dừng qlda-pg, cổng 5432 trống |
