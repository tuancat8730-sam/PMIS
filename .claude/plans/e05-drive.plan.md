# Kế hoạch: E5 Google Drive hai chiều (đọc cây thư mục, đồng bộ file, đẩy file từ app)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E5: L, phase 2, phụ thuộc E4); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 3 mục 3 (dòng 131–150), DDL `drive_files` (dòng 393–408), §2 (ARQ, Drive), §8 Phase 2 (`drive_service.py`); `CLAUDE.md` (ARQ cho Drive sync, không hard-code ID thư mục, bí mật qua biến môi trường).
**Độ phức tạp:** Lớn (tích hợp bên ngoài, worker nền mới, quota, xung đột).
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e05-drive`, tạo từ `main` sau khi E4 được merge.
**Phương pháp:** TDD. Mọi test không gọi mạng thật: Drive được bọc sau một Protocol và test dùng bản giả. Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E5 hoàn thành"

| Nhóm | Nội dung | Thuộc E5? |
|---|---|---|
| Bảng `drive_files` theo DDL spec, `drive_file_id` UNIQUE | `app/models/drive_file.py`, migration mới | ✅ Có |
| Thêm FK `draft_drive_file_id`, `signed_drive_file_id` vào `legal_documents` | Migration riêng (S3 của E4) | ✅ Có |
| Worker ARQ, khai báo job và lịch quét | `app/worker/`, `arq` trong `pyproject.toml`, service `worker` trong compose | ✅ Có |
| Cổng Drive (Protocol) và cài đặt bằng `google-api-python-client` | `app/integrations/drive.py` | ✅ Có |
| Chiều Drive → App: quét đệ quy `root_drive_folder_id`, upsert theo `drive_file_id`, phân loại định dạng | `app/services/drive_sync.py` | ✅ Có |
| Gợi ý khớp (auto-match) file với đầu mục checklist, chỉ gợi ý, không đổi trạng thái | `app/services/drive_sync.py` | ✅ Có |
| Chiều App → Drive: đẩy file sinh ra (báo cáo, biên bản, ảnh) vào đúng thư mục quy định | `app/services/drive_upload.py` | 🟡 Chỉ khung và cổng. Nội dung file thuộc E9, E10, E11 |
| Xem trước file (PDF/Docx) trên giao diện | `apps/web` | ⏸ Làm sau khi API ổn định |
| Quét thư mục đã mở rộng: xung đột hai chiều | — | ⏸ Hai chiều đầy đủ sau khi một chiều chạy ổn (xem mục 6) |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E5 được đánh ✅ khi:** migration round-trip sạch; quét lần hai không tạo bản ghi trùng (idempotent); file đổi tên hoặc đổi thời gian sửa được cập nhật, không tạo dòng mới; lỗi quota và mạng được retry có giới hạn và ghi log có ngữ cảnh; không có bí mật trong mã hay log; test chạy không cần mạng; coverage ≥ 80%; ruff sạch; OpenAPI cập nhật; plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E4 (`legal_documents`) | ⬜ | Chưa có |
| Bảng `drive_files` | ⬜ | Chưa có model |
| ARQ và Redis | ⬜ | `pyproject.toml` chưa có `arq`, `redis`. Compose đã có service `redis` (CLAUDE.md) |
| Cấu hình `root_drive_folder_id` | ⬜ | Chưa có trong `Settings`. ID nằm trong spec §7, sẽ đưa vào seed của dự án, không hard-code |
| Thông tin xác thực Google | ⬜ | Chưa có. Không được commit file khóa |
| Mẫu tích hợp bên ngoài | ⬜ | Chưa có. Mẫu cấu hình: `app/core/crypto.py` (lớp nhỏ, cấu hình qua `Settings`) |
| Mẫu test | ✅ | `tests/unit/test_crypto.py`, `tests/integration/conftest.py` |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | Spec yêu cầu "2 chiều" nhưng `pmis-epics.plan.md` ghi rủi ro "một chiều trước, hai chiều sau" | Làm một chiều trước (Drive → App, và App → Drive ở mức khung) |
| S2 | CAO | Spec không nói cách xác thực với Google (service account hay OAuth người dùng) | Hỏi Q1 |
| S3 | TB | Spec không quy định cấu trúc thư mục con chuẩn (ví dụ `5.Nghiệm thu, bàn giao`) để app đẩy file vào đúng chỗ | Hỏi Q2 |
| S4 | TB | Có hai dạng ID thư mục trong spec, cả hai dùng làm `root_drive_folder_id` | Lưu theo dự án trong DB, không trong mã |
| S5 | THẤP | `drive_files.extracted_text` và `ai_audit_summary` được điền ở E6, không ở E5 | E5 để NULL, E6 điền sau |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| Google Drive API | Quota theo người dùng và theo dự án | Quét lớn có thể bị 403/429. Cần backoff và giới hạn số lượt |
| Thư mục gốc | Quyền đọc (và ghi cho chiều App → Drive) với tài khoản dịch vụ | Thiếu quyền thì không quét được |
| Redis | Hàng đợi ARQ | Không có Redis thì worker không chạy. Compose đã có |
| Dữ liệu thật | File Drive thực tế của hai dự án | Chỉ kiểm chứng được khi có quyền. Test dùng bản giả |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | Một tài khoản dịch vụ được chia sẻ quyền đọc vào thư mục gốc của từng dự án | Nếu PM muốn OAuth người dùng, đổi cổng xác thực, không đổi nghiệp vụ |
| G2 | Quét theo lịch (ví dụ 15 phút) và nút "quét ngay" cho PM | Đổi tần suất trong cấu hình |
| G3 | Xung đột: file do người dùng tải lên trên Drive được coi là nguồn đúng, app không ghi đè | Xem Q3 |
| G4 | Chỉ đọc metadata và nội dung cần cho E6, không tải toàn bộ file khi quét | Tải nội dung theo yêu cầu |
| G5 | Lưu `drive_file_id` là khóa idempotent | Thêm khóa theo `(project_id, drive_path)` nếu cần |

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Xác thực với Google bằng gì? | Tài khoản dịch vụ, JSON khóa nạp qua biến môi trường, không commit. Chia sẻ thư mục gốc cho tài khoản này | ✅ Chốt 2026-11-01: tài khoản dịch vụ. Khóa đọc từ `~/.secrets/pmis-drive.json` (xem Q7) |
| Q2 | Cấu trúc thư mục con chuẩn trên Drive là gì? | Lấy từ thư mục thực tế của dự án (VD `5.Nghiệm thu, bàn giao`), lưu thành cấu hình theo dự án | ✅ Chốt 2026-11-01: lấy từ thư mục thực tế. Đã đọc cây SGD-HCM và SGD-LAmDong. Chấp nhận đề xuất ánh xạ loại biên bản → thư mục (dùng cho Pha 4) |
| Q3 | Xung đột khi cả hai bên cùng sửa thì xử lý thế nào? | Không ghi đè. Đánh dấu xung đột, PM chọn. Đây cũng là nguyên tắc chung của CLAUDE.md | ✅ Chốt 2026-11-01: đề xuất được chấp nhận |
| Q4 | Có tách hai chiều thành hai epic không? | Không. Một chiều ở E5, chiều App → Drive dùng chung khung của E5 | ✅ Chốt 2026-11-01: đề xuất được chấp nhận |
| Q5 | File Google Sheets gốc (không có đuôi) có đồng bộ không? | Có, xuất sang `.xlsx` | ✅ Chốt 2026-11-01: không đồng bộ, bỏ qua. Giữ phân loại theo đuôi |
| Q6 | Commit E5 thế nào? | Theo từng pha | ✅ Chốt 2026-11-01: commit theo từng pha |
| Q8 | Cách ghi lên Drive khi tài khoản dịch vụ không có quota trong My Drive | Cần chọn: (a) Shared Drive, (b) OAuth người dùng, hoặc (c) tạm chỉ đọc | ✅ Chốt 2026-11-01: OAuth người dùng (`tuan.catnghiemhieu@gmail.com`). Đọc vẫn dùng tài khoản dịch vụ. Ghi dùng token OAuth |
| Q7 | Khóa dịch vụ dùng file nào? Đã xoay khóa chưa? | `~/.secrets/pmis-drive.json` | ✅ Chốt 2026-11-01: dùng file này. ⚠ Khóa đã bị dán vào chat và **chưa xoay**. File đang quyền 644, cần `chmod 600`. Trước khi đưa lên máy chủ thật phải xoay khóa |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e05-drive` từ `main` | ⬜ | |
| 0.2 | Thêm `arq`, `redis`, `google-api-python-client`, `google-auth` vào `pyproject.toml`, ghim phiên bản | ✅ | Ghim `google-api-python-client==2.201.0`, `google-auth==2.62.0`, `arq==0.28.0` (arq kéo theo `redis`) |
| 0.3 | Baseline test, coverage, ruff, alembic head | ✅ | PostgreSQL 16 qua Colima (container `pmis-test-pg`) |

### Pha 1: Mô hình và migration
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Model `DriveFile` theo DDL, `drive_file_id` UNIQUE | ✅ | `app/models/drive_file.py` |
| 1.2 | Migration: bảng `drive_files`, FK từ `legal_documents`, cột `projects.drive_root_folder_id` | ✅ | `a7d3e9b1c5f2`, `b8e4f2a6c1d7`. Round-trip sạch trên PostgreSQL 16; `alembic check` không lệch |

### Pha 2: Cổng Drive và phân loại (unit, không mạng)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ: phân loại theo đuôi (`.docx`, `.pdf`, `.xlsx`, `.jpg`, `.m4a`), bỏ qua file không hỗ trợ | ✅ | `tests/unit/test_drive_file_kinds.py`. Phân loại theo đuôi, không theo MIME |
| 2.2 | `app/core/drive_file_kinds.py` (thuần) | ✅ | |
| 2.3 | Protocol `DriveGateway` và bản giả trong `tests/fakes/` | ✅ | `app/integrations/drive_gateway.py`, `tests/fakes/fake_drive_gateway.py` |
| 2.4 | Adapter Google trong `app/integrations/drive.py`, không có test mạng | ✅ | Test ánh xạ, phân trang, retry có backoff, từ chối ID thư mục lạ (`tests/unit/test_drive_adapter.py`). Chỉ đọc (`drive.readonly`) |

### Pha 3: Đồng bộ Drive → App
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ: quét hai lần cho cùng cây không tạo dòng trùng; file đổi tên được cập nhật | ✅ | `tests/integration/test_drive_sync_service.py` (chạy trên PostgreSQL thật) |
| 3.2 | `app/services/drive_sync.py`: duyệt đệ quy, upsert theo `drive_file_id` | ✅ | `walk_tree`, `plan_sync` (thuần), `sync_project_drive` (ghi DB, không commit). Có giới hạn độ sâu và chống vòng lặp |
| 3.3 | Gợi ý khớp theo tên file và số hiệu văn bản, không đổi `maturity_status` | ✅ | `app/core/drive_match_rules.py`; `GET /projects/{id}/drive/suggestions`. Khớp theo số hiệu trước, rồi theo 60% từ trùng |
| 3.4 | Job ARQ `sync_project_drive` và lịch quét | ✅ | `app/worker/drive_jobs.py`, `app/worker/settings.py` (quét mỗi 15 phút). Một dự án lỗi không dừng lịch quét. Service `worker` đã thêm vào compose, chưa chạy `make up` để kiểm chứng |
| 3.5 | API: `POST /projects/{id}/drive/sync` (PM, có rate limit), `GET /projects/{id}/drive/files` | ✅ | Ghi audit `drive.sync`. Trả 409 khi thiếu thư mục gốc, 503 khi chưa có khóa, 502 khi Drive lỗi |

### Pha 4: Đẩy App → Drive (khung)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ: đẩy hai lần cho cùng nội dung không tạo file trùng | ✅ | `tests/unit/test_drive_upload_service.py`: đẩy lại cùng tên thì cập nhật, không tạo mới |
| 4.2 | `app/services/drive_upload.py`: chọn thư mục theo đường dẫn từ gốc (Q2), gọi cổng `DriveWriter` | ✅ | Thiếu thư mục thì báo `DriveFolderNotFoundError`, không tự tạo thư mục. Đường dẫn là dữ liệu đầu vào, không hard-code |
| 4.3 | Adapter ghi `GoogleDriveWriter` (scope `drive`, upsert theo tên) và endpoint đẩy file | ⬜ | Chưa làm. Cần quyền `drive` đầy đủ thay vì `drive.readonly`, và cần danh sách ánh xạ đã xác nhận trước khi ghi lên Drive thật |
| 4.4 | Chạy đẩy thử lên Drive thật theo ánh xạ đã duyệt | ✅ | Đẩy `pmis-kiem-thu-ket-noi.pdf` vào `Báo cáo tuần (pmis)` của cả hai dự án, mỗi nơi hai lần: lần 1 tạo mới, lần 2 cập nhật, không trùng. File thử vẫn còn trên Drive | Chờ bạn tạo token OAuth (xem nhật ký 2026-11-01). Lần đẩy đầu bị 403 vì tài khoản dịch vụ không có quota trong My Drive. Q8 đã chốt: OAuth người dùng |

### Pha 5: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Ruff, pytest --cov ≥ 80%, `alembic check`, round-trip migration | ✅ | 261 passed, 1 skipped, coverage 86.88%. Ruff sạch. Round-trip sạch. `alembic check` không lệch |
| 5.2 | Kiểm tra bí mật: không có JSON khóa trong diff, không log token | ✅ | Quét repo: không có private key. Khóa đã dán trong chat vẫn cần xoay (xem nhật ký) |
| 5.3 | Cập nhật `pmis-epics.plan.md` và file plan này | 🟡 | File này đã cập nhật. `pmis-epics.plan.md` chưa cập nhật |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E5 | Pha |
|---|---|---|---|
| Bảng `drive_files` | ✅ | ✅ | 1 |
| Quét Drive → App idempotent | ✅ | ✅ | 3 |
| Gợi ý khớp đầu mục | ✅ | ✅ | 3 |
| Đẩy App → Drive (khung) | ⬜ | 🟡 | 4 |
| Hai chiều đầy đủ | ⬜ | ⏸ | Sau E5 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Lộ JSON khóa tài khoản dịch vụ | Biến môi trường, `.gitignore`, không log, không đưa vào image |
| CAO | Quota Drive làm quét dở dang | Backoff, giới hạn lượt, quét tăng dần, job idempotent để chạy lại |
| TB | Xung đột hai chiều ghi đè file | Q3: không ghi đè, đánh dấu xung đột |
| TB | Worker ARQ không tin cậy trong môi trường thật | Test job bằng cách gọi trực tiếp, kiểm tra compose có service worker |
| THẤP | Thư mục lồng sâu hoặc vòng lặp | Giới hạn độ sâu và theo dõi `drive_file_id` đã thấy |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec Phân hệ 3 và DDL `drive_files`. Chưa viết mã, chờ Q1–Q4 |
| 2026-11-01 (chốt) | Người dùng trả lời: Q1 tài khoản dịch vụ; Q2 thư mục thực tế, chấp nhận đề xuất ánh xạ; Q3, Q4 theo đề xuất; Google Sheets gốc bỏ qua; commit theo từng pha; khóa dùng `~/.secrets/pmis-drive.json`; làm Pha 4 ngay. Khóa đã lộ trong chat và chưa xoay |
| 2026-11-01 (đẩy thử thật) | Token OAuth lưu tại `~/.secrets/pmis-drive-oauth-token.json` (quyền 600). Đã thêm `DRIVE_OAUTH_TOKEN_FILE` vào `.env` (gitignored). Đẩy thử thật thành công ở cả hai dự án, không trùng khi đẩy lại. Chưa xóa file thử |
| 2026-11-01 (OAuth ghi Drive) | Chốt Q8: OAuth người dùng. Thêm `GoogleDriveWriter.from_oauth_token_file`, cấu hình `DRIVE_OAUTH_TOKEN_FILE`, script đăng nhập một lần `app.integrations.drive_oauth_setup` (token ghi quyền 600, ngoài repo). Ghim `google-auth-oauthlib==1.5.0`. Full suite: 281 passed, 1 skipped, coverage 87,13%, ruff sạch. **Bạn cần làm:** (1) tạo OAuth client loại Desktop trong project `ci-project-489202`, lưu JSON vào `~/.secrets/pmis-drive-oauth-client.json`; (2) chạy `./.venv/bin/python -m app.integrations.drive_oauth_setup --client-file ~/.secrets/pmis-drive-oauth-client.json --token-file ~/.secrets/pmis-drive-oauth-token.json` và đăng nhập `tuan.catnghiemhieu@gmail.com`; (3) đặt `DRIVE_OAUTH_TOKEN_FILE` trong `.env`. Lưu ý: màn hình consent ở chế độ Testing làm token hết hạn sau 7 ngày, nên cần chuyển sang In production |
| 2026-11-01 (Pha 4 tiếp) | Xong adapter ghi `GoogleDriveWriter`, ánh xạ loại file → thư mục `(pmis)`, endpoint `POST /projects/{id}/drive/uploads` (PM, rate limit, audit `drive.upload`, 422/409/502/413). Full suite: 279 passed, 1 skipped, coverage 87,08%, ruff sạch. Đẩy thử thật bị 403 do tài khoản dịch vụ không có quota trong My Drive (xem Q8) |
| 2026-11-01 (thư mục lưu trữ) | Tạo thư mục `(pmis)` trong mỗi thư mục gốc, quyền kế thừa, tài khoản dịch vụ có quyền `writer`. SGD-HCM (gốc `1Os76jS_…`): Báo cáo tuần (pmis) `1dFHHmGyYaHs8uKEgRpyilKdH4AYRfHpb`, Biên bản bàn giao (pmis) `1RGNsFDngAvRjnRaUxJ50OgSn-546jahn`, Hợp đồng (pmis) `1NPMJ-03o8-6KHGltL9gJ9_AaeOv85YQQ`, Ảnh hiện trường (pmis) `1EixrqTD0ariUgfWFV0wun5WZo-TYgAb-`. SGD-LAmDong (gốc `1pVkbl53…`): Báo cáo tuần (pmis) `1q9GHUkanfoaMo_udms0lK2-f18g9DAD4`, Biên bản bàn giao (pmis) `1GTiyVS3Ctl9p2iS9Z3XOXe7FwSDo4aLt`, Hợp đồng (pmis) `1pPWmPryBuznblVNC7lbM_JOK8EQ7R1S4`, Ảnh hiện trường (pmis) `1gf7rVDE2DYJEGkPIXaH65DFypJJ_UQo_`. Thư mục gốc HCM vẫn có liên kết công khai (reader), các thư mục mới kế thừa quyền này |
| 2026-11-01 (Pha 4) | Xong lõi Pha 4 bằng TDD: cổng `DriveWriter`, `upload_to_project_folder` (đẩy lại không trùng, thiếu thư mục thì báo lỗi). Full suite: 264 passed, 1 skipped, coverage 87,02%, ruff sạch. Chưa làm: adapter ghi và endpoint (4.3), đẩy thử lên Drive thật (4.4) |
| 2026-11-01 (sau) | Đã hoàn thành: service và API đồng bộ, gợi ý khớp, job ARQ và lịch quét, adapter Google chỉ đọc, cột `projects.drive_root_folder_id`, service `worker` trong compose. Kết quả: 261 passed, coverage 86.88%, ruff sạch, round-trip migration sạch trên PostgreSQL 16. Chưa làm: Pha 4 (đẩy file lên Drive), vì chưa chốt ánh xạ loại biên bản → thư mục đích và chưa cấp quyền ghi; kiểm chứng với Drive thật, vì khóa JSON đã lộ trong chat và cần xoay trước khi dùng; cập nhật `pmis-epics.plan.md`; chạy `make up` để kiểm chứng compose. Thư mục gốc đã xác nhận: SGD-HCM và SGD-LAmDong-Lop10. Quyền dịch vụ hiện là writer, giữ theo yêu cầu của bạn. |
| 2026-11-01 | Người dùng chốt Q1 (tài khoản dịch vụ), Q2 (lấy từ thư mục thực tế), Q3/Q4 (theo đề xuất). Nhánh `feat/e05-drive` tạo từ `feat/e04-legal` (E4 chưa merge vào `main`). Hoàn thành Pha 1 (SQL), Pha 2.1–2.3, Pha 3.2 phần thuần bằng TDD; unit test xanh (100 passed). Chưa làm: service ghi DB, job ARQ, API, adapter Google, Pha 4, Pha 5 (chưa có PostgreSQL và chưa có cây thư mục thật của Q2) |

## Acceptance

- [x] Plan đã ghi ra file
- [x] Q1–Q7 đã được chốt (cập nhật 2026-11-01)
- [ ] E5 đạt đủ điều kiện "E5 hoàn thành" ở mục 1
