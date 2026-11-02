# Kế hoạch: Quản lý file Drive theo dự án (xem trực tiếp, tự cập nhật)

**Nguồn:** `.claude/plans/e05-drive.plan.md` (E5 đã merge, mục 1 ghi "Xem trước file" là ⏸); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 3 mục 3.
**Độ phức tạp:** Trung bình–Lớn (có backend mới cho nội dung file, UI mới, và một quyết định về độ trễ đồng bộ).
**Ngày lập:** 2026-11-02.
**Nhánh dự kiến:** `feat/e05-drive-files-ui`, tạo từ `main`.
**Phương pháp:** TDD. Test Drive dùng bản giả (`tests/fakes/fake_drive_gateway.py`), không gọi mạng. Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn · ❓ chờ quyết định

## 1. Yêu cầu và phạm vi

Yêu cầu gốc (người dùng, 2026-11-02): mỗi dự án có trang quản lý file; hiển thị các file trên Google Drive; xem trực tiếp được trên tool; khi thêm file mới vào thư mục Drive thì tool cũng cập nhật theo.

| Nhóm | Nội dung | Thuộc phạm vi? |
|---|---|---|
| Trang "Tệp Drive" trong từng dự án, hiển thị cây thư mục và danh sách file | `apps/web` | ✅ |
| Tìm kiếm và lọc theo loại file (DOCX, PDF, XLSX, ảnh, âm thanh) | `apps/web` | ✅ |
| Xem trực tiếp PDF và ảnh trong tool | API stream + `apps/web` | ✅ |
| Tự cập nhật khi có file mới, đổi tên, sửa đổi, hoặc bị xóa trên Drive | worker + `drive_sync` | ✅ (xem mục 2.3) |
| Xem trực tiếp DOCX, XLSX, M4A | Cần thư viện render hoặc chuyển đổi | ❓ Q-D |
| Upload, sửa, xóa file từ tool | E5 Pha 4.3 | ⏸ Không thuộc |
| Trích xuất nội dung, AI kiểm toán | E6 | ⏸ Không thuộc |
| Google Docs, Sheets gốc (không có đuôi) | Đã chốt Q5 của E5: bỏ qua | ⏸ Không thuộc |

**Đặt tên:** trang hiện có tên "File & bằng chứng" (file register, `components/tracking/file-register-table.tsx`). Trang mới đặt tên "Tệp Drive" để không nhầm với file register.

**Hoàn thành khi:** PM và thành viên dự án xem được cây file Drive của dự án và mở được PDF, ảnh trong tool; file mới trên Drive xuất hiện trong tool sau độ trễ đã chốt ở Q-A; file bị xóa không còn hiện; dự án A không xem được file của dự án B; test và lint xanh; mobile không cuộn ngang.

## 2. Hiện trạng

### 2.1 Đã có

| Thành phần | Bằng chứng |
|---|---|
| Đồng bộ Drive → DB theo cây, idempotent theo `drive_file_id` | `apps/api/app/services/drive_sync.py` (`sync_project_drive`), `apps/api/app/core/drive_tree.py` (`walk_tree`, `plan_sync`) |
| Bảng `drive_files` có `file_name`, `drive_path`, `mime_type`, `file_size`, `web_view_link`, `modified_time` | `apps/api/app/models/drive_file.py` |
| Worker ARQ quét mỗi 15 phút | `apps/api/app/worker/settings.py` (`DRIVE_SWEEP_MINUTES`), `apps/api/app/worker/drive_jobs.py` |
| API liệt kê file và nút quét ngay (PM, có rate limit) | `apps/api/app/api/v1/drive.py`: `GET /projects/{id}/drive/files`, `POST /projects/{id}/drive/sync` |
| Phân loại định dạng theo đuôi | `apps/api/app/core/drive_file_kinds.py` |
| Adapter Drive có retry và backoff, chỉ đọc | `apps/api/app/integrations/drive.py`, scope `drive.readonly` |
| Mẫu test: unit thuần, integration trên PostgreSQL thật, bản giả Drive | `tests/integration/test_drive_sync_service.py`, `tests/fakes/fake_drive_gateway.py` |
| Tab dự án | `apps/web/src/components/tracking/project-sections.ts` |

### 2.2 Chưa có

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| UI danh sách file Drive | ⬜ | Web không gọi `GET .../drive/files`. `apps/web/src/lib/file-register.ts` chỉ dùng `drive_file_id` của file register |
| Tải nội dung file | ⬜ | `integrations/drive.py` chưa có hàm tải, `DriveGateway` chỉ có `list_children` |
| Xem trực tiếp trong tool | ⬜ | E5 ghi ⏸ |
| Xử lý file bị xóa hoặc di chuyển | ❌ | `plan_sync` chỉ phân loại tạo mới hoặc cập nhật. File đã xóa trên Drive vẫn nằm trong DB và sẽ hiện mãi |
| Cập nhật gần thời gian thực | ⬜ | Hiện chỉ quét 15 phút. Chưa dùng Drive `changes` API hay webhook |

### 2.3 Lỗ hổng cần sửa để "tự cập nhật" đúng

Khi file bị xóa hoặc chuyển ra khỏi cây dự án, `walk_tree` không trả về nó, nhưng `plan_sync` không đánh dấu. Kết quả: danh sách sẽ sai dần. Phải sửa trước khi làm UI, nếu không UI sẽ hiển thị file đã mất.

## 3. Thiết kế

### 3.1 Backend: đồng bộ đầy đủ
- Thêm cột `removed_at` (nullable, timestamptz) vào `drive_files`. Migration mới.
- `sync_project_drive` đánh dấu `removed_at = now` cho các dòng có `drive_file_id` không còn trong snapshot. Nếu file quay lại thì xóa `removed_at`.
- API liệt kê mặc định chỉ trả dòng có `removed_at IS NULL`.
- Lý do dùng đánh dấu thay vì xóa cứng: giữ lịch sử để sau này E6 và E4 có thể tham chiếu, và tránh mất liên kết với `legal_documents` đã khớp.

### 3.2 Backend: tải nội dung có kiểm soát
- Thêm `download(drive_file_id) -> Iterator[bytes]` vào Protocol `DriveGateway` và adapter (`MediaIoBaseDownload`, theo từng khối).
- Endpoint mới: `GET /projects/{project_id}/drive/files/{drive_file_id}/content`.
  - Tra file trong DB theo `project_id` và `drive_file_id`, không tìm được thì 404. Không để truy cập file của dự án khác.
  - Quyền: `ANY_PROJECT_ROLE` (chờ Q-C).
  - Chỉ cho phép loại xem trực tiếp: PDF, ảnh. Loại khác trả 415 và web hiện nút tải về (sẽ làm ở Q-D).
  - Giới hạn kích thước theo cấu hình (đề xuất 25 MB). Vượt thì trả 413. Kiểm tra `file_size` từ DB trước khi gọi Drive.
  - Trả `StreamingResponse` với `Content-Type` từ loại file, `Content-Disposition: inline`, `Cache-Control: private, no-store`, và `X-Content-Type-Options: nosniff`.
- Không dùng iframe preview của Google và không redirect sang link Drive. Lý do: người xem trong tool có thể không có quyền Google trên thư mục, và file không được nằm ngoài xác thực của app.
- Audit: ghi `drive.view` khi tải nội dung? Chờ Q-C. Mặc định không ghi, vì đọc nhiều sẽ làm audit log phình to.

### 3.3 Worker và độ trễ cập nhật
- Mặc định (G2 của E5): giữ quét 15 phút, thêm nút "Quét ngay" trên UI.
- Phương án B: lưu `changes` page token theo dự án và dùng `changes.list` thay cho duyệt toàn cây. Nhanh hơn và tốn quota ít hơn. Cần migration thêm cột token và có quy tắc khởi tạo lại khi token hết hạn.
- Phương án C: `changes.watch` (webhook). Cần endpoint HTTPS công khai, kênh hết hạn sau khoảng một tuần nên phải có job gia hạn. Phụ thuộc việc triển khai VPS (thư mục `deploy/` hiện chưa commit).
- Trong mọi phương án, UI tự làm mới danh sách khi tab được focus lại và sau khi bấm "Quét ngay".

### 3.4 Web
- Route: `apps/web/src/app/projects/[projectId]/drive/page.tsx`. Thêm tab "Tệp Drive" vào `project-sections.ts`.
- Lớp API: `apps/web/src/lib/drive-files.ts`, theo mẫu `lib/file-register.ts`, dùng `lib/api.ts`.
- Component:
  - `DriveFileList`: nhóm theo `drive_path`, tìm kiếm theo tên, lọc theo loại, cỡ và ngày sửa hiển thị theo `vi-VN`.
  - `DriveFileViewer`: dialog. PDF và ảnh được tải bằng `fetch` kèm Bearer token, rồi tạo `URL.createObjectURL`. Không dùng `<iframe src>` trực tiếp vì không gửi được header. Thu hồi URL khi đóng dialog.
  - Nút "Quét ngay" hiện với PM (hoặc mọi vai trò, chờ Q-C).
- Mobile first, nút chạm tối thiểu theo quy ước PMIS, không cuộn ngang.
- Trạng thái lỗi: 409 "Dự án chưa khai báo thư mục gốc", 503 "Máy chủ chưa cấu hình tài khoản dịch vụ", 502 "Google Drive đang từ chối yêu cầu, hãy thử lại sau". Tất cả tiếng Việt có dấu.

## 4. Kế hoạch thực hiện

Mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Chốt Q-A đến Q-D | ✅ | Xem mục 6 |
| 0.2 | Nhánh `feat/e05-drive-files-ui` từ `main` | ✅ | Đã tạo, chưa commit |
| 0.3 | Baseline: pytest, ruff, vitest, lint, alembic head | 🟡 | API: 549 passed, ruff sạch, head `c4f8a2d6e1b9`. Dùng PostgreSQL local, database `pmis_test`. Vitest và lint web chưa chạy, sẽ chạy ở Pha 3 |

### Pha 1: Đánh dấu file đã xóa (backend)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: file biến mất khỏi cây thì `removed_at` được đặt; file quay lại thì xóa `removed_at`; quét lặp không ghi thêm | ✅ | `tests/integration/test_drive_sync_service.py` |
| 1.2 | Test đỏ: API liệt kê không trả file đã `removed_at` | 🟡 | Phủ ở mức service (`list_project_drive_files`), endpoint dùng hàm này. Gợi ý khớp (`suggest_drive_matches`) cũng đã lọc nhưng chưa có test riêng |
| 1.3 | Migration thêm `removed_at`, cập nhật model và `sync_project_drive` | ✅ | Migration `d5e9b3a7f1c2`. Round-trip sạch, `alembic check` sạch, dev DB đã nâng lên head. API 554 passed, coverage 84.52%, ruff sạch |

### Pha 2: Tải nội dung file (backend)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ: file dự án khác trả 404; file không có trong DB trả 404; loại không xem được trả 415; file vượt giới hạn trả 413 | ⬜ | `tests/unit/` cho quy tắc thuần, integration cho endpoint |
| 2.2 | `download` vào Protocol, bản giả và adapter Google | ⬜ | Test adapter không gọi mạng, dùng bản giả của `MediaIoBaseDownload` |
| 2.3 | Endpoint stream với header bảo mật | ⬜ | Test header `Content-Type`, `Content-Disposition`, `Cache-Control` |
| 2.4 | Cập nhật OpenAPI | ⬜ | FastAPI tự sinh tại `/openapi.json` |

### Pha 3: Danh sách và cây file (web)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ: `lib/drive-files.ts` ánh xạ đúng response và xử lý các mã lỗi | ⬜ | Mẫu: `lib/file-register.test.ts` |
| 3.2 | Route `drive/page.tsx`, tab trong `project-sections.ts` | ⬜ | |
| 3.3 | `DriveFileList`: cây, tìm kiếm, lọc loại, nút "Quét ngay", tự làm mới khi focus | ⬜ | Mẫu: `file-register-table.test.tsx` |

### Pha 4: Xem trực tiếp (web)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ: viewer gọi `fetch` với Bearer token và thu hồi object URL khi đóng | ⬜ | |
| 4.2 | `DriveFileViewer` cho PDF và ảnh; loại khác hiện nút tải về | ⬜ | Thêm DOCX, XLSX nếu chốt Q-D |
| 4.3 | Kiểm tra mobile width, không cuộn ngang | ⬜ | Playwright, mẫu `e2e/tracking-pages.spec.ts` |

### Pha 5: Độ trễ cập nhật (tùy theo Q-A)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Nếu chọn B: `changes` token theo dự án, migration, test khởi tạo lại khi token hết hạn | ⏸ | Chỉ làm nếu Q-A chọn B |
| 5.2 | Nếu chọn C: endpoint webhook, xác thực kênh, job gia hạn | ⏸ | Chỉ làm nếu Q-A chọn C, cần HTTPS công khai |

### Pha 6: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | `make api-test` với coverage ≥ 80%, `make api-lint`, `make web-test`, `make web-lint`, `make web-build` | ⬜ | |
| 6.2 | Kiểm tra bí mật: không có khóa, không log token | ⬜ | |
| 6.3 | Cập nhật `pmis-epics.plan.md` (E5) và file plan này | ⬜ | |
| 6.4 | Commit theo từng pha, không tự merge PR | ⬜ | Chỉ khi người dùng yêu cầu |

## 5. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Lộ file dự án cho người không có quyền | Kiểm tra `project_id` ở mọi truy vấn, test 404 cho dự án khác, không redirect sang Drive |
| CAO | Lộ JSON khóa service account (đã dán trong chat và chưa xoay, theo E5 Q7) | Xoay khóa trước khi đưa lên máy chủ thật. Ghi chú này đã có trong E5 |
| TB | File lớn làm nặng server (audio, PDF scan) | Giới hạn 25 MB, stream theo khối, kiểm tra `file_size` trước khi gọi Drive |
| TB | Quota Drive khi nhiều người xem cùng lúc | Tải theo yêu cầu, không cache nội dung trên server ở phiên bản đầu |
| TB | File đã xóa vẫn hiện | Pha 1 xử lý trước khi làm UI |
| TB | Người dùng hiểu 15 phút là gần thời gian thực | Hiển thị "Cập nhật lúc HH:mm" lấy từ `last_synced_at`, và nút "Quét ngay" |
| THẤP | Nhầm với trang "File & bằng chứng" | Đặt tên "Tệp Drive" và mô tả riêng trong tab |

## 6. Câu hỏi cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q-A | Độ trễ cập nhật khi có file mới trên Drive là bao nhiêu? | **A (khuyến nghị):** giữ quét 15 phút, thêm nút "Quét ngay". Ít thay đổi nhất. B: `changes` API, khoảng 1–2 phút. C: webhook, gần thời gian thực, cần HTTPS công khai | ✅ Chốt 2026-11-02: A, quét 15 phút + nút "Quét ngay". Pha 5 không làm |
| Q-B | Cách xem trực tiếp? | **Xem trong tool qua backend** (stream PDF và ảnh, đúng quyền của app). Phương án khác: mở link Google Drive, nhưng người xem cần có quyền Google trên thư mục | ✅ Chốt 2026-11-02: xem trong tool qua backend |
| Q-C | Ai được xem file, và ai được bấm "Quét ngay"? | **Mọi thành viên dự án xem được. Chỉ PM bấm "Quét ngay"** (khớp với endpoint sync hiện tại). Có ghi audit khi xem không? Đề xuất: không | ✅ Chốt 2026-11-02: mọi thành viên xem; chỉ PM bấm Quét ngay; không ghi audit khi xem |
| Q-D | Ngoài PDF và ảnh, có cần xem DOCX, XLSX trong tool không? | **Chưa.** Hai loại này chỉ tải về ở phiên bản đầu. Xem trực tiếp cần thêm thư viện render phía trình duyệt, nặng hơn đáng kể | ✅ Chốt 2026-11-02: chưa, PDF và ảnh trước |

## 7. Ghi chú
- Phạm vi đã loại trừ upload, sửa, xóa từ tool. Nếu muốn, đó là E5 Pha 4.3 và cần quyền `drive` đầy đủ.
- Nếu Q-A chọn C, phải xác nhận lại triển khai VPS trước khi làm Pha 5.
