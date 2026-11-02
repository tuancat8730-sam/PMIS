# Kế hoạch: thiết kế lại UI sáu màn hình tracking (mobile first)

**Phạm vi:** `/projects/[projectId]` gồm Mốc, Rủi ro, Pháp lý, File, Quyết định, Hợp đồng.
**Độ phức tạp:** Large (L)
**Ngày lập:** 2026-11-02
**Ngoài phạm vi:** đổi API/schema/seed, form ghi dữ liệu mới, xuất `.xlsx`, dark mode.

## Quyết định đã xác nhận

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Tông màu | Navy đậm làm primary, accent teal, màu ngữ nghĩa cho rủi ro và trạng thái |
| 2 | Quyết định, Hợp đồng | Route riêng `/decisions`, `/contracts`. `/overview` giữ thông tin chung |
| 3 | Điều hướng điện thoại | Dải tab cuộn ngang dính đầu trang |
| 4 | Dữ liệu thiếu | Hiển thị "Chưa đánh giá" / "Chưa có nguồn", không suy đoán |

## Hiện trạng (đã đọc code)

- Mỗi màn là `MatrixPage` ([matrix-page.tsx](apps/web/src/components/tracking/matrix-page.tsx)) bọc bảng 6–9 cột trong `overflow-x-auto`.
- Chưa có layout chung cho `/projects/[projectId]`.
- [globals.css](apps/web/src/app/globals.css) chỉ có hai biến màu. Body dùng Arial, ghi đè Geist.
- [layout.tsx](apps/web/src/app/layout.tsx) khai báo `Geist` với subset `latin`. Cần kiểm tra dấu tiếng Việt.
- Quyết định và Hợp đồng hiện là anchor trong [overview-view.tsx](apps/web/src/components/tracking/overview-view.tsx).
- Dữ liệu LD thiếu `impact`, `likelihood`, cột pháp lý và hành động của file register.

## Mẫu theo màn hình

| Màn | Điện thoại (<640px) | Máy tính (≥1024px) |
|---|---|---|
| Mốc | Thẻ theo mốc, chi tiết mở bằng `<details>` | Bảng gọn, cột phụ trong dòng mở rộng |
| Rủi ro | 3 KPI, heatmap 4×4 thu gọn, thẻ xếp theo điểm | Heatmap trái, bảng phải |
| Pháp lý | Thanh tóm tắt, accordion theo giai đoạn, chip lọc | Cùng accordion, đủ cột |
| File | Thẻ nhóm theo thư mục, chip pháp lý | Bảng, cột tên cố định |
| Quyết định | Thẻ theo loại, QĐ phê duyệt dự án đứng đầu | Bảng |
| Hợp đồng | Thẻ theo gói | Bảng |

**Layout chung:** `app/projects/[projectId]/layout.tsx` gồm header (mã, tên dự án) và dải sáu tab, active theo `usePathname`.

**Component dùng chung (tối thiểu):** `StatusChip`, `ProgressBar`, `StatCard`, `EmptyState`.

**Logic thuần trong `lib/`:** `riskHeatmapBuckets`, `legalStatusSummary`, ánh xạ tông màu. Viết test đỏ trước.

## Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Đổi markup làm hỏng test hiện có | Cập nhật test cùng lúc, không xóa |
| CAO | Heatmap LD toàn ô trống | Gom vào "Chưa đánh giá" |
| TB | Trang pháp lý nặng trên mobile | Accordion đóng mặc định |
| TB | Font thiếu dấu tiếng Việt | Kiểm tra subset `vietnamese` |

## Pha

### Pha 0: Khảo sát
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Lưu plan thành file md | ✅ | File này |
| 0.2 | Chụp hiện trạng ở 375px và 1280px | ✅ | Đã chụp 375px cho Mốc, Rủi ro, Pháp lý, File, Tổng quan; 1280px cho Mốc. Bảng Mốc 9 cột bị cắt ở 375px. File và Quyết định trống trên DB dev (xem nhật ký). Chưa chụp 1280px cho các màn còn lại |
| 0.3 | Đọc test vitest và `e2e/tracking-pages.spec.ts` | ✅ | e2e giữ các chuỗi: "Điều chỉnh mốc khảo sát", "Tiến độ gắt", "QĐ phê duyệt chủ trương đầu tư", tên file "1595_QD phe duyet du an...signed.pdf", "5.999.498.939 đ", "29/HĐKT-DVN". Giữ các chuỗi này hoặc cập nhật cùng lúc |

### Pha 1: Nền
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ cho hàm thuần | ⬜ | |
| 1.2 | Token trong `globals.css`, font, layout chung, 4 component | ⬜ | |

### Pha 2–5: Màn hình, mỗi màn một commit
| Pha | Màn | Trạng thái |
|---|---|---|
| 2 | Mốc | ✅ |
| 3 | Rủi ro | ✅ |
| 4 | Pháp lý, File | ✅ |
| 5 | Quyết định, Hợp đồng (route mới) | ✅ |

Chưa commit. CLAUDE.md chỉ cho commit khi người dùng yêu cầu, nên các thay đổi nằm trong working tree, chưa tách commit theo từng màn như plan gốc.

### Pha 6: Kiểm chứng
| ID | Việc | Trạng thái |
|---|---|---|
| 6.1 | vitest, tsc, eslint, next build | ✅ 125 test unit, tsc và eslint sạch, `pnpm build` thành công |
| 6.2 | Playwright ở 375px và 1280px | ✅ 18 test e2e xanh trên Desktop Chrome và Pixel 5. Kiểm tra không tràn ngang cho cả 7 màn ở 375px và 1280px. Ảnh sau: schedule 375, legal 375, risks 1280 |
| 6.3 | So ảnh trước và sau, kiểm tương phản, vùng chạm 44px | ✅ một phần: chữ ≥ 4.5:1 ở mọi cặp token; viền control nâng lên 3.6:1; tab, nút "Chi tiết", chip lọc đều `min-h-11`. Chưa đối chiếu từng cặp ảnh trước và sau, chỉ xem ảnh sau |

## Nhật ký

| Ngày | Ghi chú |
|---|---|
| 2026-11-02 | Người dùng xác nhận bốn quyết định. Bắt đầu Pha 0 |
| 2026-11-02 | Pha 0.2: đăng nhập xong. Chụp hiện trạng. Màn File ("Chưa có file nào trong danh mục") và mục Quyết định của Tổng quan ("Chưa có quyết định nào") đều trống cho LD, khớp với ghi nhớ rằng seed Pha 3–4 chưa chạy trên DB dev. Cần xác minh trước khi kết luận |
| 2026-11-02 | Pha 1 đến 5 xong trong một phiên. Sai lệch so với plan: (a) Geist không có subset `vietnamese`, dùng `latin-ext`; (b) gỡ dark mode trong `globals.css`, giao diện luôn sáng; (c) Pháp lý: giai đoạn đầu mở sẵn để hồ sơ hiện khi tải (e2e cần thấy), các giai đoạn khác đóng; (d) File: không có bảng cột tên cố định trên desktop. Dùng một danh sách dòng mở rộng, vì tên file xuất hiện hai lần trong DOM sẽ làm e2e lỗi strict mode; (e) Mốc, Rủi ro, Pháp lý, File dùng một DOM đổi theo breakpoint, không render hai bản vì cùng lý do; (f) `border-subtle` đậm lên `#7d879b` để đạt 3:1 cho viền control; (g) `/overview` không còn trong dải tab. Đã thêm tab "Tổng quan" đứng đầu dải tab và trang chủ, theo quyết định của người dùng; (h) `ProjectShell` gọi `fetchProjectOverview` để lấy mã và tên dự án, nên mỗi lần chuyển tab có thêm 3 request. Người dùng để cache sau |
