# Kế hoạch: E1 — Danh mục đa dự án, archetype, bên liên quan, nhân sự chủ chốt, hợp đồng

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (dòng E1: phân hệ P1, §4, phụ thuộc E0); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` §3 Phân hệ 1 (mục 2–3), §4.1–4.2 (bảng `projects`, `project_stakeholders`, `contracts`, `contract_personnel`), §6 (cấu trúc `api/v1/`, `services/`); `CLAUDE.md` (layering router → service → model, service không commit, audit cùng transaction, rate limit cho endpoint ghi, CCCD qua `FieldCipher`, TDD).
**Độ phức tạp:** Trung bình–Lớn (4 bảng, 4 nhóm endpoint, 1 migration). **Cập nhật lần cuối:** 2026-10-31.
**Phương pháp:** TDD: test đỏ → xanh → refactor, mỗi việc. Test tích hợp chạy trên PostgreSQL 16 thật (`pmis-e1-test`, cổng 5433, DB `pmis_test`).
**Chú giải:** ✅ xong · 🟡 xong một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E1 hoàn tất"

| Nhóm | Nội dung | Thuộc E1? |
|---|---|---|
| Bảng `projects` + archetype (`IT_SYSTEM`, `GOODS_PROCUREMENT`, `CONSTRUCTION`, `HYBRID`) | Tạo, liệt kê, xem chi tiết | ✅ Có |
| Bảng `project_stakeholders` + liên danh (kiểm tổng tỷ lệ ≤ 100%) | Thêm, liệt kê theo dự án | ✅ Có |
| Bảng `contracts` (gói thầu, giá trị, ngày ký/hết hạn) | Thêm, liệt kê theo dự án | ✅ Có |
| Bảng `contract_personnel` (CCCD mã hóa, quét trùng CCCD trong dự án) | Thêm, liệt kê theo hợp đồng | ✅ Có |
| Migration Alembic cho 4 bảng | 1 revision, có `downgrade` đã kiểm tra | ✅ Có |
| Template engine sinh M1–M9, H0–H9, CL-01..10, 89 hồ sơ | Cần bảng milestone, hold point, checklist (E3, E4) | ⏸ Hoãn |
| Seed dữ liệu thật SGD-HCM và SGD-Lâm Đồng | Epic plan xếp vào E2; số liệu còn mâu thuẫn (1.670 vs 1.732) | ⏸ Hoãn sang E2 |
| RBAC theo dự án (membership) | Cần bảng thành viên dự án; CLAUDE.md ghi "sẽ thêm ở E1" | ⏸ Quyết định ở mục 5 (D3) |
| Giao diện web cho danh mục dự án | Spec Phase 2 (Executive Dashboard) | ⏸ Hoãn |
| Các cột bảo lãnh, phạt, tạm ứng trong `contracts` | Thuộc E7 (tài chính) | ⏸ Hoãn sang E7 |

**E1 được đánh ✅ khi:** 4 nhóm endpoint đạt test (201/409/422/403/401/404); CCCD không lưu dạng rõ, quét trùng hoạt động; mọi thao tác ghi có audit cùng transaction; `alembic check` sạch và `downgrade` chạy được; ruff sạch; coverage ≥ 80%; OpenAPI có đủ endpoint mới; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu (E1) | Trạng thái | Bằng chứng |
|---|---|---|
| Baseline trước khi sửa | ✅ | 43/43 test xanh trên PostgreSQL 16, coverage 90,95% (ngưỡng 80%) |
| Layering router → service → model | ✅ | Đã áp dụng cho 4 nhóm mới (mục 4) |
| Rate limit endpoint ghi | ✅ | Mọi POST mới gắn `WriteRateLimitDep` |
| Mã hóa CCCD | ✅ | `FieldCipher` đã gắn vào `services/personnel.py` (lần đầu dùng) |
| Bảng nghiệp vụ dự án | ✅ | 4 bảng, migration `6b19966287e0` |

## 3. Mẫu cần bám theo (Patterns to Mirror)

| Hạng mục | Nguồn | Mẫu |
|---|---|---|
| Đặt tên file/router | `apps/api/app/api/v1/users.py:11` | `router = APIRouter(prefix="/users", tags=["users"])`; file theo số nhiều; mỗi router thêm vào `api/v1/__init__.py` |
| Hàm endpoint ghi | `apps/api/app/api/v1/users.py:14-20` | `payload: Schema`, `principal: Annotated[Principal, Depends(require_roles(...))]`, `session: SessionDep`, `_rate_limit: WriteRateLimitDep`, `status_code=201` |
| Lỗi nghiệp vụ | `apps/api/app/services/users.py:11` và `api/v1/users.py:33-38` | Exception riêng trong service, router đổi thành `HTTPException` với thông điệp tiếng Việt; `await session.rollback()` trước khi raise |
| Service không commit | `apps/api/app/services/users.py:24-40` | Hàm `async`, tham số keyword-only, `session.add` + `session.flush()`; router gọi `session.commit()` |
| Audit cùng transaction | `apps/api/app/api/v1/users.py:41-48` | `record_audit(session, actor_id=..., action="user.create", ...)` rồi commit |
| Schema đầu vào | `apps/api/app/schemas/base.py:4` và `schemas/users.py:6-14` | Kế thừa `RequestModel` (`extra="forbid"`), `Field(min_length, max_length)` với hằng số có tên |
| Schema đầu ra | `apps/api/app/schemas/auth.py:14-23` | `UserOut` với `from_attributes=True`, không có trường bí mật |
| Hằng số và ngưỡng | `apps/api/app/schemas/users.py:4-6`, `app/core/config.py:24-25` | Hằng số có tên; ngưỡng cấu hình qua `Settings` với `Field(gt=0)` |
| Model SQLAlchemy | `apps/api/app/models/user.py:9-30` | `Mapped[...]`, `mapped_column`, enum với `values_callable` để lưu giá trị UPPER_SNAKE |
| Mã hóa trường nhạy cảm | `apps/api/app/core/crypto.py:4-17` | `FieldCipher.encrypt/decrypt`; chỉ giải mã khi cần so khớp |
| Dependency dùng chung | `apps/api/app/api/deps.py` | `SessionDep`, `WriteRateLimitDep` là `Annotated[..., Depends(...)]`; E1 thêm `ProjectDep`, `ContractDep`, `CipherDep` theo cùng kiểu |
| Test tích hợp | `apps/api/tests/integration/test_users_api.py:1-40` | `pytestmark = pytest.mark.integration`; fixture `make_user`, `client`, `session`; AAA có comment |
| Helper dùng chung | `apps/api/tests/integration/helpers.py` | `login_as`, `create_project`, `create_contract`, `PROJECT_PAYLOAD`, `CONTRACT_PAYLOAD` |
| Test thuần (unit) | `apps/api/tests/unit/test_crypto.py:1-10` | `pytestmark = pytest.mark.unit`; không cần DB |
| Dọn bảng giữa các test | `apps/api/tests/integration/conftest.py` | Fixture autouse `clean_tables` chạy `TRUNCATE ... CASCADE`, đã thêm 4 bảng mới |
| Migration | `apps/api/migrations/versions/20261031_b9561eaced0e_*.py` | Autogenerate, rồi sửa `downgrade` để xóa enum (`sa.Enum(...).drop`) |

## 4. Files đã thay đổi

| File | Hành động | Lý do |
|---|---|---|
| `apps/api/app/models/project.py` | CREATE | Bảng `projects`, enum `ProjectArchetype`, `ProjectHealth`, hàm `enum_values` |
| `apps/api/app/models/project_stakeholder.py` | CREATE | Bảng `project_stakeholders`, enum `StakeholderRole` |
| `apps/api/app/models/contract.py` | CREATE | Bảng `contracts` |
| `apps/api/app/models/contract_personnel.py` | CREATE | Bảng `contract_personnel`, enum `PersonnelComplianceStatus`, property `national_id_masked` |
| `apps/api/app/models/__init__.py` | UPDATE | Đăng ký 4 model |
| `apps/api/migrations/versions/20261031_6b19966287e0_tao_bang_e1_danh_muc_du_an.py` | CREATE | Migration 4 bảng; `downgrade` xóa 4 enum |
| `apps/api/app/schemas/projects.py` | CREATE | `ProjectCreate` (kiểm mã, ngày, tổng mức đầu tư), `ProjectOut` |
| `apps/api/app/schemas/stakeholders.py` | CREATE | `StakeholderCreate` (tỷ lệ 0–100), `StakeholderOut` |
| `apps/api/app/schemas/contracts.py` | CREATE | `ContractCreate` (giá trị > 0, ngày), `ContractOut` |
| `apps/api/app/schemas/personnel.py` | CREATE | `PersonnelCreate` (CCCD 12 số, bỏ khoảng trắng), `PersonnelOut` (chỉ có CCCD đã che) |
| `apps/api/app/services/projects.py` | CREATE | Tạo, liệt kê, lấy theo id; lỗi trùng mã |
| `apps/api/app/services/stakeholders.py` | CREATE | Thêm bên liên quan, khóa dòng dự án, kiểm tổng liên danh |
| `apps/api/app/services/contracts.py` | CREATE | Tạo, lấy theo id, liệt kê |
| `apps/api/app/services/personnel.py` | CREATE | Mã hóa CCCD, quét trùng trong dự án, liệt kê |
| `apps/api/app/api/deps.py` | UPDATE | Thêm `ProjectDep`, `ContractDep` (404 dùng chung), `CipherDep` |
| `apps/api/app/api/v1/projects.py` | CREATE | Router `/projects`: POST, GET, GET theo id |
| `apps/api/app/api/v1/stakeholders.py` | CREATE | Router `/projects/{id}/stakeholders`: POST, GET |
| `apps/api/app/api/v1/contracts.py` | CREATE | Router `/projects/{id}/contracts`: POST, GET |
| `apps/api/app/api/v1/personnel.py` | CREATE | Router `/contracts/{id}/personnel`: POST, GET (chỉ ADMIN, PM) |
| `apps/api/app/api/v1/__init__.py` | UPDATE | Gắn 4 router mới |
| `apps/api/tests/unit/test_project_rules.py` | CREATE | Unit: tổng liên danh, tỷ lệ, mã dự án, khoảng ngày |
| `apps/api/tests/unit/test_personnel_rules.py` | CREATE | Unit: chuẩn hóa CCCD, che số |
| `apps/api/tests/integration/test_projects_api.py` | CREATE | IT dự án: 201/409/422/403/401/404, audit |
| `apps/api/tests/integration/test_stakeholders_api.py` | CREATE | IT bên liên quan và liên danh |
| `apps/api/tests/integration/test_contracts_api.py` | CREATE | IT hợp đồng |
| `apps/api/tests/integration/test_personnel_api.py` | CREATE | IT nhân sự: mã hóa, che số, cảnh báo trùng, quyền, audit không chứa CCCD |
| `apps/api/tests/integration/helpers.py` | UPDATE | Thêm `PROJECT_PAYLOAD`, `CONTRACT_PAYLOAD`, `create_project`, `create_contract` |
| `apps/api/tests/integration/conftest.py` | UPDATE | `clean_tables` truncate thêm 4 bảng mới |
| `.claude/plans/pmis-epics.plan.md` | UPDATE | Trạng thái E1 |

## 5. Quyết định (theo mặc định, người dùng yêu cầu thực hiện)

| # | Quyết định | Lý do | Trạng thái |
|---|---|---|---|
| D1 | Tên cột CCCD: `national_id_encrypted` (Text, Fernet) và `national_id_last4` (VARCHAR 4) để hiển thị | Spec ghi `national_id_cccd` nhưng lưu dạng rõ là vi phạm CLAUDE.md. `last4` cho phép hiển thị mà không giải mã | ✅ |
| D2 | Quét trùng CCCD bằng cách giải mã và so khớp trong các nhân sự của cùng dự án, không dùng blind index | Số nhân sự mỗi dự án nhỏ. Tránh thêm khóa thứ hai và HMAC chưa cần (YAGNI). Rủi ro ở mục 9 | ✅ |
| D3 | RBAC theo dự án: bảng `project_members` (dự án, người dùng, vai trò trong dự án). ADMIN toàn cục vượt qua mọi kiểm tra. Người tạo dự án thành PM của dự án. Đọc dự án, bên liên quan, hợp đồng: thành viên bất kỳ vai trò. Ghi dự án, bên liên quan, hợp đồng, thêm thành viên: PM của dự án. Nhân sự (PII): đọc và ghi chỉ PM của dự án. Vai trò ADMIN không gán được làm thành viên | Người dùng duyệt: "RBAC theo dự án (D3): yesm làm đi" | ✅ Đã làm (Pha 8) |
| D4 | Trùng CCCD: không chặn, lưu với `compliance_status = DUPLICATE_ID_WARNING` và trả cờ trong response | Spec yêu cầu "tự động chạy rule kiểm tra" và cảnh báo, không nói chặn | ✅ |
| D5 | Template archetype ở E1: chỉ lưu và kiểm enum `archetype`, không sinh khung M1–M9/H0–H9/89 hồ sơ | Các bảng đích thuộc E3 và E4 | ✅ |
| D6 | Tiền dùng `NUMERIC(18,2)` và `Decimal` trong Python, không dùng float | Tiền đầu tư công, tránh sai số | ✅ |
| D7 | Không commit, không push, không tạo nhánh mới | CLAUDE.md: commit chỉ khi người dùng yêu cầu. Nhánh `feat/e01-*` theo quy định phải tạo từ `main`, nhưng `main` local không có E0; xem mục 9 | ✅ |
| D8 | Bảng `contracts` không có `status`, `guarantee_*`, `penalty_*`, `advance_*`, `stakeholder_id` | Các cột này thuộc E7 hoặc chưa có nhu cầu ở E1 | ✅ |
| D9 | Router tách theo tài nguyên: `projects.py`, `stakeholders.py`, `contracts.py`, `personnel.py` thay vì một file | Mỗi file ngắn, dễ đọc. Khác bản kế hoạch ban đầu (mục 4 ghi gộp) | ✅ |
| D10 | Kiểm 404 của dự án và hợp đồng qua dependency `ProjectDep`, `ContractDep` trong `deps.py` | Tránh lặp logic 404 ở 4 router. Đúng mẫu `SessionDep` | ✅ |
| D11 | Khi thêm liên danh có tỷ lệ, khóa dòng dự án bằng `SELECT ... FOR UPDATE` trước khi tính tổng | Hai request đồng thời không cùng vượt 100% | ✅ |
| D12 | Mã hóa CCCD qua `CipherDep` lấy từ `Settings.cccd_encryption_key`, tạo `FieldCipher` mỗi request | Đơn giản, đủ cho E1. Có thể chuyển sang `app.state` nếu cần | ✅ |

## 6. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor. Chạy lệnh từ `apps/api` với `TEST_DATABASE_URL=postgresql+asyncpg://pmis:pmis@localhost:5433/pmis_test`.

### Pha 0 – Baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Ghi plan này | ✅ | |
| 0.2 | PostgreSQL test | ✅ | Container `pmis-e1-test` cổng 5433, DB `pmis_test` |
| 0.3 | Baseline | ✅ | 43/43 xanh, coverage 90,95% |

### Pha 1 – Model và migration
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Model 4 bảng và enum, đăng ký trong `models/__init__.py` | ✅ | Xem D9 |
| 1.2 | Sinh migration bằng autogenerate, sửa `downgrade` để xóa 4 enum | ✅ | Autogenerate không xóa enum; đã thêm tay (cùng lỗi với migration E0) |
| 1.3 | `upgrade head`, `downgrade`, `upgrade head`, `alembic check` | ✅ | `No new upgrade operations detected.` Enum được tạo lại sau round-trip |

### Pha 2 – Dự án (archetype, mã duy nhất)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ IT: tạo 201, mã trùng 409, sai ngày 422, archetype sai 422, PM_CONSULTANT 403, audit `project.create`, list, get, 404, 401 | ✅ | Đỏ 10/11 (sau khi có bảng, lỗi là 404/405 thật). 1 test xanh sẵn: `unknown_project_returns_404`, vì 404 mặc định khi chưa có route; vẫn đúng sau khi có route |
| 2.2 | Test đỏ unit: mã sai định dạng, khoảng ngày | ✅ | Gộp vào `tests/unit/test_project_rules.py`. Đỏ vì `ModuleNotFoundError` |
| 2.3 | Schema, service, router `/projects` | ✅ | 11/11 xanh |
| 2.4 | Refactor, cập nhật `clean_tables` | ✅ | Thêm `ProjectDep` (D10). Bỏ bản sao `PROJECT_PAYLOAD` |

### Pha 3 – Bên liên quan và liên danh
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ unit: tổng liên danh > 100 bị từ chối; tỷ lệ âm và > 100 bị từ chối | ✅ | Đỏ vì thiếu `app.schemas.stakeholders` |
| 3.2 | Test đỏ IT: 201, liên danh vượt 100 → 422, 100 đúng → 201, dự án không có → 404, audit, 403, list | ✅ | |
| 3.3 | Service, router `/projects/{id}/stakeholders`, khóa dòng dự án (D11) | ✅ | 28/28 xanh cùng test dự án |

### Pha 4 – Hợp đồng
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ IT: 201, giá trị ≤ 0 → 422, hết hạn trước ngày ký → 422, list, 404, audit | ✅ | |
| 4.2 | Service, router `/projects/{id}/contracts` | ✅ | 6/6 xanh |

### Pha 5 – Nhân sự chủ chốt (CCCD)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Test đỏ unit: chuẩn hóa CCCD (bỏ khoảng trắng, 12 số); che 4 số cuối | ✅ | Đỏ vì thiếu `app.schemas.personnel` |
| 5.2 | Test đỏ IT: response không có CCCD đủ; cột DB không chứa CCCD rõ; trùng trong dự án → cảnh báo; khác dự án → VERIFIED; sai định dạng → 422; list chỉ có số che; audit không chứa CCCD; PM_CONSULTANT → 403; hợp đồng không tồn tại → 404 | ✅ | |
| 5.3 | Service, router `/contracts/{id}/personnel`, `CipherDep` (D12) | ✅ | 16/16 xanh (unit + IT) |

### Pha 6 – Kiểm chứng
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | `ruff check`, `ruff format --check` | ✅ | Sạch sau khi sửa 1 dòng dài, sắp import, đổi `_enum_values` thành `enum_values` (dùng chéo giữa các module) |
| 6.2 | `pytest --cov`: toàn bộ xanh, coverage ≥ 80% | ✅ | 93/93 xanh, coverage 90,52% |
| 6.3 | `alembic check` và migration round-trip | ✅ | Round-trip sạch, `alembic check` không drift |
| 6.4 | Kiểm OpenAPI | ✅ | `/projects`, `/projects/{id}`, `/projects/{id}/stakeholders`, `/projects/{id}/contracts`, `/contracts/{id}/personnel` đều có |
| 6.5 | Tự review: không secret, không `print` mới, không mutate tham số, hàm ngắn | ✅ | `print` còn lại trong `app/cli.py` có từ E0. Không có `print` mới |

### Pha 7 – Đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 7.1 | Cập nhật `pmis-epics.plan.md` (E1) | ✅ | |
| 7.2 | Dọn: không commit | ✅ | Theo D7 (đã đổi, xem Pha 9) |

### Pha 8 – RBAC theo dự án (D3, người dùng duyệt)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 8.1 | Test đỏ IT `test_project_access.py` (17 test): thành viên, PM không phải thành viên, danh sách theo thành viên, ADMIN, thêm thành viên, 409, 404, 422 với ADMIN, audit, quyền stakeholder/contract/personnel | ✅ | Đỏ 8/17. 9 test xanh sẵn vì hành vi vai trò toàn cục trùng kỳ vọng mới (ví dụ CONTRACTOR không ghi được bên liên quan) |
| 8.2 | Model `ProjectMember`, migration `72cef211f6aa` (có xóa enum trong `downgrade`) | ✅ | Round-trip và `alembic check` sạch |
| 8.3 | `services/memberships.py`, guard `ensure_project_role` / `project_role_guard` / `contract_role_guard` trong `deps.py` | ✅ | ADMIN bỏ qua kiểm tra |
| 8.4 | Router `project_members.py` (POST, GET); người tạo dự án thành PM | ✅ | |
| 8.5 | Chuyển stakeholders, contracts, personnel sang guard theo dự án; danh sách dự án lọc theo thành viên | ✅ | Bỏ kiểm `require_roles` toàn cục ở các endpoint này |
| 8.6 | Ruff, coverage, migration | ✅ | 110/110 xanh, coverage 89,89% |

### Pha 9 – Nhánh và PR (người dùng yêu cầu)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 9.1 | Nhánh `feat/e01-portfolio` từ `origin/main` (đã có E0 qua PR #1 `733433d`) | ✅ | Thay đổi E1 được stash rồi áp lại |
| 9.2 | Commit theo file cụ thể, không `git add -A` | ⬜ | |
| 9.3 | Push `-u origin feat/e01-portfolio` và tạo PR vào `main` | ⬜ | |

## 7. Kết quả kiểm chứng (2026-10-31)

| Kiểm tra | Kết quả |
|---|---|
| `pytest --cov` | 93 passed, 0 failed; coverage tổng 90,52% (ngưỡng 80%) |
| Test mới | 50 test (43 baseline → 93) |
| `ruff check` | All checks passed |
| `ruff format --check` | 68 files already formatted |
| `alembic upgrade head` → `downgrade b9561eaced0e` → `upgrade head` | Chạy được; enum được tạo lại |
| `alembic check` | No new upgrade operations detected |
| OpenAPI | 5 path mới đúng method |

Chưa kiểm: `docker compose up` với migration E1 (cần chạy lại stack để xác nhận; không nằm trong DoD E1 nhưng nên làm trước khi merge).

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E1 | Pha |
|---|---|---|---|
| Dự án và archetype | ✅ | ✅ | 1, 2 |
| Bên liên quan và liên danh | ✅ | ✅ | 3 |
| Hợp đồng | ✅ | ✅ | 4 |
| Nhân sự chủ chốt và CCCD | ✅ | ✅ | 5 |
| Migration sạch | ✅ | ✅ | 1, 6 |
| RBAC theo dự án | ✅ | ✅ | 8 |
| Commit và PR vào `main` | ⬜ | ✅ | 9 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | CCCD là PII. Nếu log hoặc response lộ CCCD đầy đủ thì vi phạm CLAUDE.md | Chỉ lưu bản mã hóa và `last4`; không đưa CCCD vào log hay `changes` của audit; test kiểm cột DB, response, audit |
| TB | Không thành viên nhận 403 cho dự án tồn tại nhưng 404 cho UUID không có, nên có thể dò được sự tồn tại của dự án | Chấp nhận ở E1; UUID v4 khó đoán. Cân nhắc trả 404 chung cho cả hai trường hợp ở epic sau |
| TB | Người tạo dự án được thêm làm PM mà không có dòng audit riêng `project_member.add` (gộp trong `project.create`) | Ghi chú trong code; nếu cần audit tách, thêm một dòng ở epic sau |
| TB | Đổi `CCCD_ENCRYPTION_KEY` làm `decrypt` ném `InvalidToken` khi quét trùng, gây lỗi 500 khi thêm nhân sự | Chưa xử lý ở E1. Ghi nhận; cần quy trình xoay khóa và xử lý lỗi rõ ràng ở epic sau |
| TB | Quét trùng CCCD giải mã toàn bộ nhân sự của dự án (D2) | Chấp nhận ở E1; nếu số lượng lớn, thêm blind index HMAC ở epic sau |
| TB | Nhánh: CLAUDE.md yêu cầu tạo `feat/e01-*` từ `main`, nhưng `main` local không có E0 | Làm E1 trên `feat/e00-foundation` hiện tại, không commit. Người dùng quyết định cách tách nhánh khi commit |
| TB | Số liệu thực tế chưa chốt (1.670 vs 1.732) | Không seed trong E1 (mục 1) |
| THẤP | Migration E1 chưa chạy trên `docker compose up` | Chạy lại stack trước khi commit |
| THẤP | Coverage theo file `auth.py` còn lệch (F5 của E0) | Ghi nhận, không xử lý trong E1 |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Đọc plan epic, spec §3 (phân hệ 1), §4.1–4.2, §6, §7; code API và test hiện có. Baseline 43/43 xanh, coverage 90,95%. Viết plan này |
| 2026-10-31 | Pha 2 (TDD): test đỏ dự án (lỗi thật: bảng chưa tồn tại) → model và migration (Pha 1) → test đỏ 10/11 do 404/405 → schema, service, router → 11/11 xanh |
| 2026-10-31 | Pha 1: downgrade thiếu xóa enum, sửa tay trước khi chạy. Round-trip và `alembic check` sạch |
| 2026-10-31 | Pha 3: test đỏ `ModuleNotFoundError: app.schemas.stakeholders` → khóa dòng dự án, kiểm liên danh → 28/28 xanh |
| 2026-10-31 | Pha 4: 6/6 xanh ngay sau khi có router |
| 2026-10-31 | Pha 5: test đỏ `ModuleNotFoundError: app.schemas.personnel` → mã hóa CCCD, quét trùng, che số → 16/16 xanh |
| 2026-10-31 | Pha 6: ruff sửa 3 lỗi (dòng dài, import, tên hàm private dùng chéo). Toàn bộ 93/93 xanh, coverage 90,52%. Migration round-trip sạch |
| 2026-10-31 | Sửa một lỗi trong test trùng CCCD: biến `project_id` gán nhầm, dùng hàm chưa tồn tại. Viết lại test tự dựng dữ liệu |
