# Kế hoạch: E2 Đơn vị thụ hưởng, tên kép sau sáp nhập, cụm địa lý

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E2: S, phase 1, phụ thuộc E0, E1); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` §2 (Phân hệ 2, dòng 118–128), §3 Phân hệ 6 mục 3 (dòng 189–190), §4.2 DDL `beneficiary_units` (dòng 340–362), §7 Seed (dòng 616–630); `CLAUDE.md` (layering, audit cùng transaction, dữ liệu khóa, TDD, AAA).
**Độ phức tạp:** Nhỏ về mã (Small); trung bình khi tính seed (Medium), vì seed bị chặn bởi dữ liệu 62 trường chưa có (xem B1).
**Ngày lập:** 2026-10-31.
**Phương pháp:** rà soát tĩnh `apps/api` (E1 đã merge vào `main`, commit `89ba1f7`), đối chiếu spec. Thực hiện theo TDD: test đỏ → xanh → refactor. Chưa viết mã; plan này chờ người dùng xác nhận.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E2 hoàn thành"

| Nhóm | Nội dung | Thuộc E2? |
|---|---|---|
| Bảng `beneficiary_units` (đơn vị thụ hưởng, tên cũ/mới, cụm, đầu mối) | `app/models/beneficiary_unit.py`, migration mới | ✅ Có |
| API CRUD đơn vị theo dự án, lọc theo cụm và loại trường | `app/api/v1/beneficiary_units.py` | ✅ Có |
| Hiển thị kép "Tên mới (Tên cũ)" dùng chung cho API và biên bản sau này | `display_dual_name()` trong service | ✅ Có |
| Seed 8 đơn vị khảo sát TP.HCM (spec §7) | `app/db/seed_real_projects.py` + file dữ liệu | ✅ Có |
| Seed 62 đơn vị Lâm Đồng, 4 cụm | Cùng script | ❌ Bị chặn: chưa có danh sách (B1) |
| Seed hai dự án `SGD-HCM-CSVC-2026` và `SGD-LD-TB10-2026` (chỉ thông tin dự án) | Cùng script | ✅ Có, theo §7 |
| Ma trận 62×4×3, lịch giao hàng 3 đợt | — | ⏸ E9 |
| Lịch xe, nhân sự Tổ nghiệm thu/TVGS đi theo cụm | — | ⏸ E9 (Phân hệ 2 mục 2) |
| Mốc tiến độ, hold point, lịch khảo sát theo đơn vị | — | ⏸ E3, E8 |
| Giao diện web (trang danh sách trường và cụm) | `apps/web` | ⏸ Làm sau khi API ổn định, không thuộc DoD backend của E2 |
| Commit, push, merge PR | — | ⏸ Chỉ làm khi người dùng yêu cầu (CLAUDE.md) |

**E2 được đánh ✅ khi:** migration round-trip sạch và `alembic check` không drift; API có test xanh (đọc, ghi, 403, 404, 409, audit); seed idempotent chạy hai lần cho ra cùng số bản ghi; coverage ≥ 80%; ruff sạch; plan epic được cập nhật. Riêng mục seed Lâm Đồng chỉ đánh ✅ khi B1 được giải quyết.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Bảng đơn vị thụ hưởng | ⬜ | Không có model hay migration nào liên quan (`apps/api/app/models/` chỉ có user, project, contract, stakeholder, personnel, member, audit) |
| Dự án đã có để gắn đơn vị | ✅ | `projects` và `project_stakeholders` từ E1, migration `6b19966287e0` |
| RBAC theo dự án | ✅ | `project_role_guard`, `ANY_PROJECT_ROLE` trong `app/api/deps.py` |
| Audit trong cùng transaction | ✅ | `record_audit` trong `app/services/audit.py` (cho phép `actor_id=None` cho thao tác hệ thống) |
| Rate limit thao tác ghi | ✅ | `WriteRateLimitDep` trong `app/api/deps.py` |
| Dữ liệu 62 trường Lâm Đồng | ❌ | Repo không có file xlsx/csv/docx nào. Spec chỉ có số lượng theo cụm và vài ví dụ tên (B1) |
| Dữ liệu 8 đơn vị TP.HCM | ✅ có trong spec | Spec §7 dòng 626 liệt kê đủ 8 tên. Chưa có mã đơn vị (B3) |

## 3. Dữ liệu và mâu thuẫn cần xác nhận (chặn hoặc ảnh hưởng)

| ID | Mức | Vấn đề | Đề xuất xử lý |
|---|---|---|---|
| B1 | CAO | Thiếu danh sách 62 đơn vị Lâm Đồng: mã, tên hiện tại, tên cũ, cụm, xã/phường, đầu mối. Spec chỉ có số lượng 15/19/14/14 và 2 ví dụ | Người dùng cung cấp file (xlsx hoặc csv) theo mẫu cột ở D8. Trong lúc chờ: làm xong code, migration, API, seed TP.HCM. Không bịa tên trường |
| B2 | TB | Tên cụm không khớp giữa spec: §3 dòng 125 ghi "Cụm 1 Cư Jút – Đắk Mil – Krông Nô", "Cụm 2 Đắk Song – Gia Nghĩa – Đắk Glong". §7 dòng 626 ghi "Cụm 1: 15 đơn vị Bắc Đắk Nông cũ", "Cụm 2: 19 đơn vị Nam Đắk Nông cũ". Tên theo địa bàn và tên theo tỉnh cũ không cùng một tiêu chí | Lưu cả `cluster_code` (Cụm 1..4, theo §7) và `cluster_name` (theo địa bàn, lấy từ dữ liệu thật). Không suy đoán tên địa bàn |
| B3 | TB | Spec không cho mã đơn vị TP.HCM | Đặt `unit_code` tạm `HCM-01`..`HCM-08` theo thứ tự §7, đánh dấu tạm trong dữ liệu. Đổi khi có mã thật |
| B4 | TB | Số trường mâu thuẫn: 1.670 (§1.1, §5.1) và 1.732 (KPI §5.1). E2 seed nên chốt số trước | Không ảnh hưởng schema. Hỏi người phụ trách trước khi seed; không tự chọn |
| B5 | TB | Định dạng tên kép không thống nhất. DDL §4.2 ghép `official (former)`. Ví dụ §3 dòng 123 ghi `THPT Phan Bội Châu (THPT Nguyễn Bỉnh Khiêm cũ)` có chữ "cũ" | Xem quyết định D1. Cần người dùng chốt mẫu hiển thị theo thể thức công văn |

## 4. Quyết định (đề xuất, chờ xác nhận)

| # | Quyết định đề xuất | Lý do | Nếu đổi |
|---|---|---|---|
| D1 | Bỏ cột `GENERATED` `display_dual_name` trong DDL. Tính trong Python bằng hàm thuần `display_dual_name(official, former)`. Mẫu hiển thị chốt theo B5 | Một nguồn sự thật, test unit được. Cột generated dễ gây drift với `alembic check`. DDL spec ghép không có chữ "cũ", ví dụ spec có | Nếu muốn cột DB, thêm `Computed(persisted=True)` và kiểm `alembic check` |
| D2 | Cụm là hai cột trên đơn vị (`cluster_code`, `cluster_name`), không tạo bảng `clusters` | YAGNI. Spec không yêu cầu thuộc tính riêng cho cụm ở E2. Lọc và nhóm bằng `cluster_code` | Tách bảng khi E9 cần lịch xe và nhân sự theo cụm |
| D3 | Một `former_name` cho mỗi đơn vị | Spec DDL chỉ có một cột. Đa số trường trong danh sách là một tên cũ | Thêm bảng `beneficiary_unit_former_names` nếu có trường gộp từ nhiều đơn vị |
| D4 | Ràng buộc duy nhất `(project_id, unit_code)`. Trùng trả 409 với thông điệp tiếng Việt | Mã đơn vị là khóa nghiệp vụ trong một dự án. Khớp mẫu `DuplicateMemberError` | — |
| D5 | API: `POST` và `PATCH` cần vai trò PM (đúng `stakeholders`). `GET` cho mọi thành viên dự án. Lọc `cluster_code`, `unit_type` trên `GET` danh sách. Không phân trang ở E2 | Quy mô ~62 đơn vị mỗi dự án, không cần phân trang | Thêm phân trang khi số bản ghi vượt ~500 |
| D6 | Đầu mối: một đầu mối chính, theo cột `focal_point_*` của DDL. Hiệu trưởng ở `principal_name` | Khớp spec. Nhiều đầu mối (CNTT, CSVC, tổ trưởng) thuộc E9 | Tách bảng `unit_contacts` khi E9 cần |
| D7 | Seed đi qua service, không ghi SQL trực tiếp. Upsert theo `(project_id, unit_code)`, audit với `actor_id=None` | Chạy lại không nhân đôi. Có audit, đúng quy ước thao tác hệ thống | — |
| D8 | Mẫu cột file dữ liệu Lâm Đồng: `unit_code, cluster_code, cluster_name, unit_type, official_name, former_name, district_or_commune, former_province, address, principal_name, focal_point_name, focal_point_role, focal_point_phone` | Trùng với cột DDL. Người dùng điền theo mẫu | — |
| D9 | `PATCH` được phép sau khi đơn vị đã `ACCEPTED`, nhưng ghi audit `changes` theo từng trường. Khóa dữ liệu đã nghiệm thu thuộc E9 | Chưa có quy trình nghiệm thu ở E2. Tránh khóa cứng sớm | Khóa khi E9 có trạng thái nghiệm thu và biên bản ký |
| D10 | Ràng buộc miền bằng `StrEnum`: `UnitType` (THPT, THCS, TIEU_HOC, PTDTNT, GDTX, UBND_PHUONG), `ReadinessStatus` (PENDING, CONFIRMED, SURVEYED, DELIVERED, ACCEPTED). Lưu chuỗi UPPER_SNAKE theo CLAUDE.md | Khớp mẫu `StakeholderRole` và quy ước spec | — |
| D11 | Migration thêm hai enum mới. `downgrade` phải `DROP TYPE` cho cả hai | Bài học từ migration E0: autogenerate không tự xóa enum | — |

## 5. Pattern cần bám theo (Pattern Grounding)

| Hạng mục | Nguồn | Mẫu |
|---|---|---|
| Đặt tên | `apps/api/app/models/project_stakeholder.py`, `app/services/stakeholders.py`, `app/api/v1/stakeholders.py`, `app/schemas/stakeholders.py` | Model số ít theo tên bảng số nhiều. Service theo động từ. Router theo tài nguyên, prefix `/projects/{project_id}/...` |
| Enum | `apps/api/app/models/project_stakeholder.py:9-20` và `enum_values` tại `app/models/project.py:27` | `StrEnum` và `Enum(..., values_callable=enum_values)` |
| Lỗi nghiệp vụ | `apps/api/app/services/stakeholders.py:15` (`ConsortiumShareExceededError`), `apps/api/app/api/v1/stakeholders.py:32-37` (422) | Service ném exception riêng. Router bắt, `rollback`, trả `HTTPException` với thông điệp tiếng Việt |
| Trùng khóa | `apps/api/app/services/memberships.py:11` và `:36` | `IntegrityError` được bắt khi `flush`, đổi thành exception nghiệp vụ |
| Khóa đồng thời | `apps/api/app/services/stakeholders.py:25` (`_lock_project`) | Chỉ dùng khi có ràng buộc tổng; E2 không cần vì ràng buộc là duy nhất theo khóa |
| Transaction và audit | `apps/api/app/api/v1/stakeholders.py:39-50` | Router gọi `record_audit` rồi `session.commit()`. Service không commit |
| Schema | `apps/api/app/schemas/stakeholders.py:17-30` | `RequestModel` (`extra="forbid"`), `Field(min_length, max_length)` với hằng số có tên |
| Phân quyền | `apps/api/app/api/deps.py` (`project_role_guard`, `ANY_PROJECT_ROLE`) | Ghi `Role.PM`, đọc `ANY_PROJECT_ROLE` |
| Rate limit ghi | `apps/api/app/api/deps.py` (`WriteRateLimitDep`) | Gắn vào mọi endpoint `POST`/`PATCH` |
| Test unit | `apps/api/tests/unit/test_project_rules.py:21-56` | Hàm thuần, tên mô tả hành vi, không DB |
| Test tích hợp | `apps/api/tests/integration/test_stakeholders_api.py:10,28,56` | `pytestmark = integration`, helper `_pm_with_project`, `make_user`, `_bearer` |
| Dọn bảng | `apps/api/tests/integration/conftest.py:79-84` | Fixture `autouse` `TRUNCATE` danh sách bảng. **Phải thêm `beneficiary_units`** |

Không có mẫu nào cho seed hay đọc file dữ liệu trong repo. Seed sẽ là mẫu đầu tiên, nên giữ đơn giản: file JSON trong `app/db/seed_data/`, đọc bằng `json` của stdlib.

## 6. Files cần thay đổi

| File | Hành động | Lý do |
|---|---|---|
| `apps/api/app/models/beneficiary_unit.py` | CREATE | Model và hai enum (D10) |
| `apps/api/app/models/__init__.py` | UPDATE | Import model để Alembic thấy bảng |
| `apps/api/migrations/versions/<ts>_<rev>_tao_bang_beneficiary_units.py` | CREATE | Migration có `downgrade` `DROP TYPE` (D11) |
| `apps/api/app/schemas/beneficiary_units.py` | CREATE | Schema create, update (từng trường tùy chọn), out |
| `apps/api/app/services/beneficiary_units.py` | CREATE | `create`, `list` có lọc, `get`, `update`, `DuplicateUnitError`, `display_dual_name` (D1) |
| `apps/api/app/api/v1/beneficiary_units.py` | CREATE | Router `/projects/{project_id}/beneficiary-units` |
| `apps/api/app/api/v1/__init__.py` | UPDATE | Include router |
| `apps/api/app/db/seed_real_projects.py` | CREATE | Script seed idempotent (D7) |
| `apps/api/app/db/seed_data/hcm_survey_units.json` | CREATE | 8 đơn vị TP.HCM, mã tạm (B3) |
| `apps/api/app/db/seed_data/lam_dong_units.json` | CREATE sau khi có B1 | 62 đơn vị Lâm Đồng |
| `apps/api/tests/unit/test_beneficiary_units_rules.py` | CREATE | Tên kép, số lượng theo cụm, miền enum |
| `apps/api/tests/integration/test_beneficiary_units_api.py` | CREATE | CRUD, 403, 404, 409, audit, lọc |
| `apps/api/tests/integration/test_seed_real_projects.py` | CREATE | Seed chạy hai lần cho cùng số bản ghi |
| `apps/api/tests/integration/conftest.py` | UPDATE | Thêm `beneficiary_units` vào `TRUNCATE` |
| `Makefile` / `README.md` | UPDATE (nhỏ) | Lệnh chạy seed (`python -m app.db.seed_real_projects`) |
| `.claude/plans/pmis-epics.plan.md` | UPDATE khi làm xong | Trạng thái E2 |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0 – Chuẩn bị
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Ghi plan này | ✅ | |
| 0.2 | Xác nhận các quyết định D1–D11 và các mục B1–B5 | ✅ | Chờ người dùng |
| 0.3 | Tạo nhánh `feat/e02-beneficiary` từ `main` mới nhất | ✅ | Theo CLAUDE.md. Sau khi xác nhận |
| 0.4 | Khởi động PostgreSQL 16 cho test (cổng 5433, theo F7 của E0) và chạy baseline API | ✅ | Kỳ vọng: 110/110 xanh (số từ E1) |

### Pha 1 – Mô hình và migration
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ `test_beneficiary_units_rules.py`: `display_dual_name` có và không có tên cũ | ✅ | Đỏ: `ModuleNotFoundError` |
| 1.2 | Model `BeneficiaryUnit` và enum `UnitType`, `ReadinessStatus`; import trong `models/__init__.py` | ✅ | |
| 1.3 | Migration: tạo bảng, unique `(project_id, unit_code)`, index `project_id`, `cluster_code`. `downgrade` drop bảng và hai enum | ✅ | |
| 1.4 | Kiểm migration: upgrade, downgrade, upgrade; `alembic check` sạch | ✅ | |
| 1.5 | Thêm `beneficiary_units` vào `TRUNCATE` trong conftest | ✅ | Không làm thì test sau bị dữ liệu cũ |

### Pha 2 – Service và API
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ IT: PM tạo đơn vị (201); trùng mã (409); lọc theo cụm; đọc được với vai trò thành viên; tư vấn không ghi được (403); dự án không tồn tại (404); có bản ghi audit với actor; PATCH có audit `changes` | ✅ | Đỏ: 404 hoặc `ModuleNotFoundError` |
| 2.2 | Schema `BeneficiaryUnitCreate`, `BeneficiaryUnitUpdate`, `BeneficiaryUnitOut` (có `display_dual_name`); hằng số độ dài | ✅ | `unit_code` giới hạn độ dài, không cho khoảng trắng đầu cuối |
| 2.3 | Service: `create_unit`, `list_units`, `get_unit`, `update_unit`; `DuplicateUnitError` bắt từ `IntegrityError` khi flush | ✅ | Service không commit |
| 2.4 | Router và include trong `v1/__init__.py`; `POST`/`PATCH` có `WriteRateLimitDep` và `record_audit` cùng transaction | ✅ | |
| 2.5 | Chạy IT xanh; kiểm OpenAPI `/openapi.json` có endpoint mới | 🟡 | |

### Pha 3 – Seed dữ liệu thật
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ unit: 8 đơn vị HCM; 62 đơn vị Lâm Đồng chia 15/19/14/14; mã không trùng trong một dự án | 🟡 | Phần Lâm Đồng đỏ đến khi có B1 |
| 3.2 | Đọc schema tạo dự án của E1 để điền đúng trường cho hai dự án theo §7 | ✅ | Trước khi viết seed |
| 3.3 | File `hcm_survey_units.json` (8 đơn vị, mã tạm `HCM-01..08`) | ✅ | Không bịa tên ngoài spec |
| 3.4 | File `lam_dong_units.json` (62 đơn vị) | ❌ | **Bị chặn B1**: chờ danh sách từ người dùng |
| 3.5 | `seed_real_projects.py`: tìm hoặc tạo dự án theo mã, tạo đơn vị còn thiếu theo `(project_id, unit_code)` (bản đã có được bỏ qua, không cập nhật), audit `actor_id=None` | ✅ | Dữ liệu nằm trong file, không hard-code trong logic |
| 3.6 | IT: chạy seed hai lần, số bản ghi không đổi; dự án và đơn vị đúng số lượng | ✅ | |

### Pha 4 – Kiểm chứng
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | `ruff check` và `ruff format --check` | ✅ | |
| 4.2 | `pytest --cov` trên PostgreSQL 16; coverage ≥ 80% | ✅ | |
| 4.3 | `alembic check` và round-trip migration | ✅ | |
| 4.4 | Tự review diff: không secret, không `print`, không dữ liệu thật trong log, hàm dưới 50 dòng | 🟡 | Theo `coding-style.md`, `security.md` |
| 4.5 | Review bảo mật: endpoint ghi có rate limit và RBAC; đầu vào được validate; không lộ chi tiết DB trong lỗi | 🟡 | Bắt buộc vì có endpoint ghi |

### Pha 5 – Đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Cập nhật mục E2 trong `pmis-epics.plan.md` | ✅ | Cùng thay đổi |
| 5.2 | Ghi lệnh seed vào README | ✅ | |
| 5.3 | Commit khi người dùng yêu cầu | ✅ | CLAUDE.md |

## 8. Trạng thái theo yêu cầu (đích cần đạt)

| Yêu cầu | Hiện tại | Đích E2 | Pha |
|---|---|---|---|
| Bảng và migration | ✅ | ✅ | 1 |
| API đọc/ghi và RBAC | ✅ | ✅ | 2 |
| Tên kép | ✅ | ✅ | 1, 2 |
| Cụm địa lý | ✅ | ✅ (thuộc tính, không có lịch) | 1, 2 |
| Seed 8 đơn vị TP.HCM | ✅ | ✅ | 3 |
| Seed 62 đơn vị Lâm Đồng | ❌ | ✅ | 3 (chờ B1) |
| Seed dự án TP.HCM | ✅ | ✅ | 3 |
| Seed dự án Lâm Đồng (cần TMĐT, xem câu hỏi) | ❌ | ✅ | 3 (chờ B1, TMĐT) |
| Coverage ≥ 80%, ruff, alembic | ✅ (89,39%) | ✅ | 4 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Thiếu dữ liệu 62 trường: seed không đầy đủ, deadline M8 30/11 | B1: xin file ngay. Làm phần không phụ thuộc trước. Không bịa tên |
| CAO | Tên kép sai thể thức công văn | D1 và B5: chốt mẫu trước khi viết hàm. Test mẫu với ví dụ §3 |
| TB | Tên cụm không khớp (B2) làm sai nhóm khi E9 xuất biên bản theo cụm | Lưu `cluster_code` theo §7 làm khóa nhóm, `cluster_name` chỉ để hiển thị |
| TB | Trường gộp nhiều tên cũ (D3) | Ghi nhận. Thêm bảng khi có dữ liệu thật |
| TB | Migration có enum mới, downgrade thiếu `DROP TYPE` | Test round-trip ở 1.4 |
| TB | Test dùng dữ liệu cũ vì quên `TRUNCATE` bảng mới | Bước 1.5 |
| THẤP | Seed chạy hai lần tạo bản ghi trùng | D7 upsert và IT 3.6 |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Đọc plan epic, spec Phân hệ 2, §4.2, §7. Rà soát E1 (`stakeholders`, `memberships`, `deps`, `audit`). Xác nhận không có dữ liệu 62 trường trong repo (B1). Ghi nhận mâu thuẫn tên cụm (B2) và mẫu tên kép (B5). Viết plan này, chưa viết mã |
| 2026-10-31 | Chốt B1–B5, D3, D9 theo trả lời của người dùng. Tạo nhánh `feat/e02-beneficiary` từ `main`. Baseline 110/110 xanh trên PostgreSQL 16 (container `pmis-e1-test`, cổng 5433, dùng lại) |
| 2026-10-31 | Pha 1 (TDD): unit đỏ `ModuleNotFoundError` → `display_dual_name` 3/3 xanh. Model `BeneficiaryUnit` và hai enum. Migration `2a5dbfd319bf`: round-trip sạch, enum được `DROP TYPE` khi downgrade, `alembic check` không drift. Thêm bảng vào `TRUNCATE` |
| 2026-10-31 | Pha 2 (TDD): 9 IT đỏ (1 test 404 xanh giả vì route chưa có, kiểm lại sau khi có guard: xanh thật). Schema, service, router `/projects/{id}/beneficiary-units`. Sửa import vòng schema ↔ service: service nhận `dict`, không import schema. Thêm test GET một đơn vị sau khi viết endpoint (không đúng thứ tự TDD, ghi nhận) → 11/11 xanh |
| 2026-10-31 | Pha 3: unit seed đỏ (module chưa có) → 8 đơn vị TP.HCM và `seed_real_projects.py` xanh; test Lâm Đồng skip có lý do B1. IT seed: 3/3 xanh ngay từ lần chạy đầu vì module đã có (không đỏ trước). Lệnh `make seed-projects`, mục README |
| 2026-10-31 | Pha 4: 130 xanh, 1 skip (B1), coverage 89,39%, ruff sạch, `alembic check` không drift. Số dòng coverage theo file của `services/beneficiary_units.py` không khớp code (nghi `.pyc` cũ); không xác minh được vì lệnh xóa cache bị chặn. Nhánh 409 được chứng minh bằng test hành vi xanh |
| 2026-10-31 | Cập nhật trạng thái plan trước khi commit. Mục chưa kiểm: `/openapi.json` (2.5), tự review đầy đủ (4.4), review bảo mật chính thức (4.5) |
| 2026-10-31 | Lệch so với D7: seed chỉ bỏ qua bản ghi đã có, không cập nhật. Chạy seed trên DB test: lần 1 thêm 7 (HCM-01 còn sót từ test API), lần 2 thêm 0 |
