# Plan: Cập nhật tiến độ mốc, ghi chú và task con

**Phạm vi:** màn `/projects/[projectId]/schedule` ("Kế hoạch và tiến độ"). Cho phép sửa từng mốc (hạn điều chỉnh, ngày hoàn thành, % hoàn thành, trạng thái), ghi chú theo mốc, và task con (thêm, sửa, xóa, đổi trạng thái).
**Độ phức tạp:** Large (L)
**Ngày lập:** 2026-11-02
**Trạng thái:** ĐÃ TRIỂN KHAI Pha 0–4 (chưa commit). Còn kiểm tra thủ công trên DB dev (4.4).

**Ngoài phạm vi:** sửa thời hạn gốc (`baseline_end`), tạo mốc mới từ giao diện, phân quyền theo dự án (theo spec ở E1), xuất file, chế độ offline của E10.

## Yêu cầu đã hiểu

1. Trên mỗi mốc, PM sửa được:
   - **Thời hạn:** hạn điều chỉnh (`adjusted_end`). Hạn gốc giữ nguyên.
   - **Cập nhật hoàn thành:** ngày hoàn thành thực tế (`actual_end`).
   - **% hoàn thành** (`progress_percent`, 0–100).
   - **Trạng thái** (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`).
2. Mỗi mốc có **ghi chú** (nhiều dòng, có thời gian và người viết).
3. Mỗi mốc có **task con**. Sửa được tên, đổi trạng thái, thêm và xóa.

## Quyết định (đã xác nhận)

| # | Câu hỏi | Đã chọn |
|---|---|---|
| 1 | Task con lưu ở đâu? | Bảng `milestone_tasks` mới, độc lập với `parent_id` |
| 2 | Ghi chú hoạt động thế nào? | Nhật ký `milestone_notes`: chỉ thêm, không sửa, không xóa, có người viết và thời gian |
| 3 | % hoàn thành tính thế nào? | Nhập tay. Task không tự đổi % |
| 4 | Ai được ghi? | TVGS (`SUPERVISION_CONSULTANT`) và PM ghi ghi chú và task. **Chỉ PM** sửa hạn, ngày hoàn thành, % và trạng thái mốc |
| 5 | Trường task con | Tên, trạng thái, người phụ trách (chuỗi tự do), hạn hoàn thành, ghi chú riêng |
| 6 | Xóa task con | PM và TVGS xóa cứng, có audit `milestone_task.delete` |

## Sai khác so với plan ban đầu

| Mục | Plan | Thực tế | Lý do |
|---|---|---|---|
| Form | `react-hook-form` | `useState` + Zod (đã có sẵn) | Không thêm dependency mới cho 3 form nhỏ |
| Vai trò trên client | Claim `role` trong JWT | Vai trò dự án từ `GET /members` khớp với `sub`. `ADMIN` toàn cục lấy từ JWT | Claim `role` là vai trò toàn cục, không phải vai trò trong dự án |
| Nạp task và ghi chú | `selectinload` | Hai truy vấn gom bằng `IN`, gom trong Python | Số câu SQL không tăng theo số mốc (có test đếm) |
| Đăng ký `Role` cho TVGS | Kiểm tra tên | `Role.SUPERVISION_CONSULTANT` | Xác nhận trong `app/core/rbac.py` |
| Router | Hai file | Hai file `milestone_tasks.py`, `milestone_notes.py` | Đúng plan |

## Pha

Mỗi việc: test đỏ trước, rồi code tối thiểu. Không commit (CLAUDE.md chỉ commit khi người dùng yêu cầu).

### Pha 0: Xác nhận
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Người dùng trả lời quyết định | ✅ | Xem bảng Quyết định |
| 0.2 | Baseline `pytest` và `vitest` trước khi sửa | ✅ | Backend: 17 test milestone xanh trên `pmis_test`. Web: 125 test |

### Pha 1: Backend, task và ghi chú
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: quy tắc quá hạn task | ✅ | `tests/unit/test_milestone_task_rules.py`, 4 test |
| 1.2 | Test đỏ: API task và ghi chú | ✅ | `tests/integration/test_milestone_children_api.py`, 10 test (quyền, 404 khác dự án, audit, ghi chú không sửa/xóa được) |
| 1.3 | Model, migration, `alembic check`, `downgrade` | ✅ | Migration `e6a0c4b8d2f7`. `alembic check` sạch. Downgrade rồi upgrade chạy đúng |
| 1.4 | Service, router, audit, rate limit | ✅ | `app/api/v1/milestone_tasks.py`, `app/api/v1/milestone_notes.py` |
| 1.5 | Kiểm tra quyền và audit | ✅ | Gộp trong 1.2 |

### Pha 2: Schedule matrix
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ: matrix có `tasks` và `notes`, số câu SQL không tăng theo số mốc | ✅ | `tests/integration/test_schedule_matrix_children_api.py`, 2 test |
| 2.2 | Thêm `tasks`, `notes` vào `ScheduleRow` (backend và `lib/tracking.ts`) | ✅ | `ScheduleRowOut` trong `app/schemas/tracking.py` |

### Pha 3: Frontend
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ: Zod, quyền, `x/y task xong` | ✅ | `milestone-forms.test.ts`, `milestone-permissions.test.ts` |
| 3.2 | `milestone-api.ts` và test | ✅ | 8 test, `fetchImpl` giả |
| 3.3 | Form sửa mốc, danh sách task, ghi chú, tích hợp | ✅ | `milestone-edit-form.tsx`, `task-list.tsx`, `note-list.tsx`, `schedule-table.tsx`, `use-project-access.ts`. Trang schedule làm lại dữ liệu bằng `reloadKey` |
| 3.4 | Ẩn form theo vai trò | ✅ | Sửa mốc chỉ PM. Task và ghi chú: PM và TVGS |

### Pha 4: Kiểm chứng
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Lint, test, build | ✅ | Backend: `ruff` sạch, 592 test xanh, coverage 84% (ngưỡng 80%). Web: `tsc` sạch, `lint` sạch, 205 test vitest xanh, `pnpm build` thành công (trang schedule 224 kB) |
| 4.2 | Playwright 375px và 1280px | ✅ | `e2e/schedule-progress.spec.ts` (PM thêm task, TVGS không thấy form mốc). `e2e/tracking-pages.spec.ts` vẫn xanh. Tổng 22 test trên Desktop Chrome và Pixel 5 |
| 4.3 | OpenAPI có endpoint mới | ✅ | `/notes`, `/tasks`, `/tasks/{task_id}` có trong schema |
| 4.4 | Thử trên DB dev | ⬜ | Chưa làm. Cần chạy `make api-migrate` trên DB dev trước khi kiểm tra tay |

## Tiêu chí chấp nhận

- [x] PM sửa được hạn điều chỉnh, ngày hoàn thành, %, trạng thái của mốc. Lỗi quy tắc hiển thị tiếng Việt.
- [x] PM và TVGS thêm, sửa, xóa task (xóa cứng). Mốc hiển thị "x/y task xong".
- [x] PM và TVGS thêm ghi chú. Ghi chú không sửa được, không xóa được, hiển thị mới nhất trước.
- [x] Chỉ PM sửa được hạn, ngày hoàn thành, % và trạng thái mốc.
- [x] Task có người phụ trách, hạn hoàn thành, ghi chú riêng. Task trễ hạn được đánh dấu.
- [x] Vai trò khác chỉ xem, không thấy form. API trả 403 khi ghi sai quyền.
- [x] Mọi thao tác ghi có audit trong cùng transaction.
- [x] Test, lint, build xanh. Coverage backend 84%.

## Rủi ro

| Mức | Rủi ro | Trạng thái |
|---|---|---|
| CAO | Vai trò trên client không khớp server | Đã giảm: UI lấy vai trò dự án từ `GET /members`, server vẫn chặn thật |
| CAO | Đổi `progress_percent` hoặc `status` mốc đã khóa làm lệch hold point | Giữ nguyên quy tắc `update_milestone` (không đổi) |
| TB | Migration trên VPS chạy `alembic upgrade head` khi deploy | Có `downgrade`. Chưa chạy trên VPS |
| TB | Số task và ghi chú tăng, matrix chậm | Gom bằng `IN`, có test số câu SQL. Chưa phân trang |
| TB | Trùng ghi chú khi bấm nhiều lần | Nút khóa khi đang gửi. Có rate limit ở API |
| THẤP | Mock E2E thiếu endpoint gây lỗi "Failed to fetch" | Đã sửa mock |

## Nhật ký

| Ngày | Ghi chú |
|---|---|
| 2026-11-02 | Đọc code: PATCH mốc đã có, màn Mốc chỉ đọc, chưa có task con. Lập plan |
| 2026-11-02 | Người dùng chọn: bảng task mới, nhật ký ghi chú chỉ thêm, % nhập tay, PM và TVGS được ghi |
| 2026-11-02 | Làm rõ: TVGS chỉ ghi ghi chú và task. Task có người phụ trách, hạn, ghi chú riêng. PM và TVGS xóa cứng task |
| 2026-11-02 | Pha 1 xong: migration, model, service, router, test. 14 test mới xanh |
| 2026-11-02 | Pha 2 xong: matrix có task và ghi chú. Test số câu SQL xanh. Full backend 592 test, coverage 84% |
| 2026-11-02 | Pha 3 xong: lib, form, component, tích hợp. Web: 205 vitest, tsc, lint, build xanh |
| 2026-11-02 | Pha 4: 22 Playwright xanh. Lỗi layout: ô trạng thái task chiếm hết chỗ, đã sửa. Lỗi "Failed to fetch" do mock E2E thiếu endpoint project, đã sửa |
