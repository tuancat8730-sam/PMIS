# Kế hoạch: Quản lý file Drive theo dự án (xem trực tiếp, tự cập nhật)

**Nguồn:** `.claude/plans/e05-drive.plan.md` (E5 đã merge, mục 1 ghi "Xem trước file" là ⏸); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` Phân hệ 3 mục 3.
**Độ phức tạp:** Trung bình–Lớn.
**Ngày lập:** 2026-11-02. **Trạng thái:** Pha 0–4 và 6 xong; Pha 5 hoãn (không cần, xem mục 6).
**Nhánh:** `feat/e05-drive-files-ui` (đã push). Commit theo pha: `d306dd3` (Pha 1), `c26f7c3` (Pha 2), `3a25cd3` (Pha 3), `52a5aa5` (Pha 4).
**Phương pháp:** TDD. Test Drive dùng bản giả, không gọi mạng. Kiểm thử đọc thật (chỉ đọc) đã chạy một lần bằng khóa dịch vụ.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn · ❓ chờ quyết định

## 1. Yêu cầu và phạm vi

Yêu cầu gốc (người dùng, 2026-11-02): mỗi dự án có trang quản lý file; hiển thị các file trên Google Drive; xem trực tiếp được trên tool; khi thêm file mới vào thư mục Drive thì tool cũng cập nhật theo.

| Nhóm | Nội dung | Trạng thái |
|---|---|---|
| Trang "Tệp Drive" trong từng dự án, cây thư mục và danh sách file | `apps/web` | ✅ Pha 3 |
| Tìm kiếm và lọc theo loại file | `apps/web` | ✅ Pha 3 |
| Xem trực tiếp PDF và ảnh trong tool | API stream + `apps/web` | ✅ Pha 2, 4 |
| Tải về DOCX, XLSX, M4A | API `download=true` + nút "Tải về" | ✅ Pha 4 |
| Tự cập nhật (file mới, đổi tên, sửa, xóa) | worker 15 phút, nút "Quét ngay", đánh dấu đã xóa | ✅ Pha 1, 3 |
| Upload, sửa, xóa file từ tool | E5 Pha 4.3 | ⏸ Ngoài phạm vi |
| Trích xuất nội dung, AI kiểm toán | E6 | ⏸ Ngoài phạm vi |
| Google Docs, Sheets gốc (không có đuôi) | Đã chốt Q5 của E5: bỏ qua | ⏸ Ngoài phạm vi |

**Đặt tên:** trang mới tên "Tệp Drive", khác với "File & bằng chứng" (file register).

**Hoàn thành khi:** PM và thành viên xem được cây file và mở được PDF, ảnh trong tool; file mới trên Drive xuất hiện sau tối đa 15 phút hoặc ngay sau "Quét ngay"; file đã xóa không còn hiện; dự án A không xem được file dự án B; test, lint, build xanh; không cuộn ngang ở 375px.

## 2. Hiện trạng ban đầu (trước khi làm)

| Thành phần | Trạng thái lúc bắt đầu |
|---|---|
| Đồng bộ Drive → DB theo cây, idempotent theo `drive_file_id` | ✅ có (E5) |
| Worker ARQ quét 15 phút, API liệt kê và quét ngay | ✅ có (E5) |
| UI danh sách file Drive | ⬜ không có |
| Tải và xem nội dung | ⬜ không có (E5 ghi ⏸) |
| Xử lý file đã xóa hoặc di chuyển | ❌ `plan_sync` không đánh dấu, file cũ hiện mãi |

## 3. Thiết kế đã triển khai

### 3.1 Đồng bộ đầy đủ (Pha 1)
- Cột `removed_at` (nullable) trong `drive_files`, migration `d5e9b3a7f1c2`.
- `plan_sync` trả thêm `to_remove`; file quay lại thì được khôi phục.
- Danh sách và gợi ý khớp bỏ qua file đã xóa.
- API `POST /drive/sync` trả thêm trường `removed`.

### 3.2 Tải nội dung (Pha 2, 4)
- `DriveGateway.download(drive_file_id) -> bytes`, adapter Google dùng `files().get_media(...).execute()` có retry.
- **Thay đổi so với bản gốc:** không stream theo khối mà đọc toàn bộ nội dung vào bộ nhớ. Bù lại bằng giới hạn 25 MB, kiểm tra `file_size` trước khi tải, và kiểm tra lại độ dài sau khi tải. Lý do: đơn giản hơn, và giới hạn đã chặn rủi ro bộ nhớ.
- Endpoint `GET /projects/{id}/drive/files/{drive_file_id}/content`:
  - Kiểm tra file thuộc dự án và chưa bị xóa (404 nếu không).
  - Mặc định (`inline`): chỉ PDF và ảnh (415 với loại khác).
  - `?download=true` (`attachment`): mọi loại đã đồng bộ, dùng cho nút "Tải về". Thay đổi này bổ sung cho bản gốc để Q-D được thực hiện đúng.
  - Header: `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff`, `Content-Disposition` với tên UTF-8.
- Không dùng iframe của Google hay redirect sang Drive (người xem có thể không có quyền Google).
- Không ghi audit khi xem (Q-C).

### 3.3 Cập nhật tự động (Pha 3)
- Worker 15 phút (giữ nguyên, Q-A) và nút "Quét ngay" (PM).
- Trang tự tải lại khi cửa sổ lấy lại focus, và sau khi quét xong.

### 3.4 Web
- `lib/drive-files.ts`: fetch danh sách, quét ngay (thông điệp tiếng Việt theo mã HTTP), tải nội dung dạng blob, nhóm theo thư mục, lọc, định dạng.
- `components/drive/`: `DriveSyncBar`, `DriveFileGroups`, `DriveFileViewer` (hộp thoại; PDF và ảnh qua object URL, thu hồi khi đóng; nút "Tải về"), `DriveFilesView` (container).
- Route `/projects/[projectId]/drive`, tab "Tệp Drive" sau tab "File".

## 4. Kế hoạch thực hiện và trạng thái

### Pha 0: Chuẩn bị
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Chốt Q-A đến Q-D | ✅ | Mục 6 |
| 0.2 | Nhánh `feat/e05-drive-files-ui` từ `main` | ✅ | |
| 0.3 | Baseline API, web, migration | ✅ | API 549 pass lúc bắt đầu. PostgreSQL local, database `pmis_test` |

### Pha 1: Đánh dấu file đã xóa (backend)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: file biến mất thì `removed_at` được đặt; quay lại thì xóa; quét lặp không ghi thêm | ✅ | `test_drive_sync_service.py`, `test_drive_tree_rules.py` |
| 1.2 | Test đỏ: API liệt kê không trả file đã xóa | 🟡 | Phủ ở mức service. Gợi ý khớp đã lọc nhưng chưa có test riêng |
| 1.3 | Migration, model, `sync_project_drive` | ✅ | Round-trip sạch, `alembic check` sạch, dev DB đã lên head |

### Pha 2: Tải nội dung (backend)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ: 404, 415, 413, 403, 502 | ✅ | `test_drive_content_api.py`, `test_drive_preview_rules.py` |
| 2.2 | `download` vào Protocol, bản giả, adapter Google | ✅ | `test_drive_adapter_download.py` |
| 2.3 | Endpoint stream với header bảo mật | ✅ | Kiểm tra trong test API |
| 2.4 | OpenAPI | ✅ | FastAPI tự sinh |

### Pha 3: Danh sách và cây file (web)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ: `lib/drive-files` | ✅ | `drive-files.test.ts` |
| 3.2 | Route và tab | ✅ | `project-home-view.test.tsx` cập nhật thứ tự tab có chủ đích (tab Drive không thuộc sheet Excel) |
| 3.3 | Component danh sách, quét ngay, tự làm mới | ✅ | `drive-sync-bar.test.tsx`, `drive-file-groups.test.tsx`, `drive-files-view.test.tsx` |

### Pha 4: Xem trực tiếp (web)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Test đỏ: fetch có token, thu hồi object URL | ✅ | `drive-files.test.ts` (fetch blob), `drive-file-viewer.test.tsx`. Việc thu hồi URL nằm trong cleanup của effect, được kiểm chứng bằng E2E |
| 4.2 | Viewer PDF, ảnh; tải về mọi loại | ✅ | Bổ sung cờ `download` ở API (mục 3.2) |
| 4.3 | Mobile 375px, không cuộn ngang | ✅ | `e2e/drive-files.spec.ts`, 5 kịch bản × desktop và mobile |

### Pha 5: Độ trễ cập nhật
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Drive `changes` API | ⏸ | Q-A chốt phương án A (quét 15 phút + nút quét ngay). Không làm |
| 5.2 | Webhook `changes.watch` | ⏸ | Không làm |

### Pha 6: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 6.1 | API: pytest, coverage, ruff, migration | ✅ | 576 pass, coverage 84.59%, ruff sạch, `alembic check` sạch |
| 6.1 | Web: vitest, lint, tsc, build | ✅ | 169 test pass, lint sạch, `tsc` sạch, `pnpm build` thành công |
| 6.1 | E2E toàn bộ | ✅ | 42 pass (kể cả các spec cũ) |
| 6.2 | Kiểm tra bí mật | ✅ | Quét diff của nhánh: không có khóa, token, client secret |
| 6.2b | Kiểm thử đọc thật trên Drive (chỉ đọc) | ✅ | Liệt kê 52 file hỗ trợ trong cây SGD-HCM và tải PDF: `%PDF-`, cỡ khớp metadata. Xác nhận `get_media().execute()` trả về bytes |
| 6.3 | Cập nhật `pmis-epics.plan.md` (E5) | ✅ | Xem mục 8 |
| 6.4 | Commit theo pha và push | ✅ | Chưa merge PR (theo quy ước repo) |

## 5. Rủi ro (còn lại)

| Mức | Rủi ro | Trạng thái |
|---|---|---|
| CAO | Lộ khóa service account (đã dán trong chat, chưa xoay theo E5 Q7; người dùng chỉ thị không xoay) | Chấp nhận theo chỉ thị. Ghi nhận lại trước khi đưa lên máy chủ thật |
| TB | Dự án chưa có `drive_root_folder_id` trong DB dev | Cần nhập ID trước khi dùng thật (xem mục 7) |
| TB | File lớn làm nặng bộ nhớ server | Giới hạn 25 MB, kiểm tra hai lần |
| THẤP | Trễ 15 phút bị hiểu nhầm là thời gian thực | Hiển thị "Cập nhật lúc" và nút "Quét ngay" |

## 6. Quyết định đã chốt

| # | Câu hỏi | Quyết định |
|---|---|---|
| Q-A | Độ trễ cập nhật | A: quét 15 phút + nút "Quét ngay" |
| Q-B | Cách xem | Xem trong tool qua backend |
| Q-C | Quyền | Mọi thành viên xem, chỉ PM quét ngay, không ghi audit khi xem |
| Q-D | Định dạng xem trực tiếp | PDF và ảnh xem trong tool; loại khác tải về |

## 7. Việc còn lại trước khi dùng thật
- Nhập `drive_root_folder_id` cho các dự án trong DB (hiện trống cho cả SGD-HCM và SGD-LD). ID đã có trong spec §Phân hệ 3; chưa nhập để tránh đổi dữ liệu dev khi chưa được yêu cầu.
- Đưa lên máy chủ thật: xoay khóa service account (E5 Q7) và `chmod 600` file khóa.
- Merge PR: chỉ khi người dùng yêu cầu.

## 8. Nhật ký và cập nhật liên quan
- 2026-11-02: Pha 0–1 commit `d306dd3`, push. Pha 2 `c26f7c3`. Pha 3 `3a25cd3`. Pha 4 `52a5aa5`.
- Kiểm thử đọc thật: script chỉ đọc trong scratchpad, không nằm trong repo.
- `pmis-epics.plan.md` (E5): cập nhật dòng E5 để phản ánh tính năng này.
