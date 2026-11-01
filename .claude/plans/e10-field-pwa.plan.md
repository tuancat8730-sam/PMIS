# Kế hoạch: E10 Mobile PWA hiện trường (quét QR/serial, ảnh có GPS, ký biên bản)

**Nguồn:** `.claude/plans/pmis-epics.plan.md` (E10: M, phase 3, phụ thuộc E9); `PROJECT_MANAGEMENT_SOFTWARE_SPEC.md` §5.5 (dòng 540–546), Phân hệ 6 mục 3 (giao diện tại điểm trường, dòng 193–197), §8 Phase 3 (`/field/[projectId]`); `CLAUDE.md` (Quy ước Thiết bị hiện trường: `Idempotency-Key`, `X-Device-Id`, xung đột không ghi đè, nút chạm 56 dp, thao tác đạt/không đạt tối đa 3 lần chạm, UI tiếng Việt).
**Độ phức tạp:** Trung bình–Lớn (ngoại tuyến, đồng bộ, camera, GPS, idempotency ở API).
**Ngày lập:** 2026-10-31.
**Nhánh dự kiến:** `feat/e10-field-pwa`, tạo từ `main` sau khi E9 được merge.
**Phương pháp:** TDD. Hàng đợi đồng bộ và quy tắc idempotency viết thuần và có test. Kiểm trên thiết bị giả lập và một máy thật (Q6). Chưa viết mã; chờ người dùng chốt mục 6.
**Chú giải:** ✅ xong · 🟡 một phần · ⬜ chưa làm · ⏸ hoãn (có quyết định) · ❌ bị chặn

## 1. Phạm vi và điều kiện "E10 hoàn thành"

| Nhóm | Nội dung | Thuộc E10? |
|---|---|---|
| Bảng `idempotency_keys` và dependency cho lệnh ghi từ thiết bị | `app/models/idempotency_key.py`, `app/api/deps.py` | ✅ Có |
| Xung đột đồng bộ: trả 409 kèm bản hiện tại, không ghi đè | `app/services/field_sync.py` | ✅ Có |
| Ảnh hiện trường: kiểm MIME bằng nội dung file, giới hạn kích thước, lưu cục bộ trước, tách EXIF GPS | `app/services/field_photos.py`, `app/core/exif_gps.py` | ✅ Có |
| Ảnh biên bản đã ký: gắn vào `delivery_handovers.signed_scan_drive_id` (cục bộ trước, Drive sau E5) | Dùng E9 | ✅ Có |
| PWA: manifest, service worker, trang `/field/[projectId]` | `apps/web/src/app/field/` | ✅ Có |
| Chọn cụm và trường (hiển thị tên mới và tên cũ) | `apps/web` | ✅ Có |
| Quét QR/barcode serial thùng máy và màn hình để đối chiếu danh sách giao | `apps/web` | ✅ Có |
| Hàng đợi offline trong IndexedDB, gửi lại theo `Idempotency-Key` | `apps/web/src/lib/field-queue.ts` | ✅ Có |
| Đánh dấu đạt, không đạt, ký biên bản trong tối đa 3 lần chạm | `apps/web` | ✅ Có |
| Đẩy ảnh và biên bản lên Drive thời gian thực | E5 | ⏸ Thuộc E5 |
| Kiểm tra ảnh AI | E6 | ⏸ Thuộc E6 |
| Commit, push, merge PR | — | ⏸ Chỉ khi người dùng yêu cầu |

**E10 được đánh ✅ khi:**
- Lệnh ghi gửi lại với cùng `Idempotency-Key` trả đúng kết quả cũ, không tạo bản ghi thứ hai (có test tích hợp).
- Hai thiết bị sửa cùng một trường cùng lúc: thiết bị sau nhận 409 kèm trạng thái hiện tại, dữ liệu không bị ghi đè.
- Ảnh không phải ảnh thật (đổi đuôi file) bị từ chối; ảnh vượt giới hạn bị từ chối; GPS đọc được khi ảnh có EXIF.
- Chạy được ngoại tuyến: tạo thao tác khi mất mạng, bật mạng lại thì gửi đủ và đúng một lần.
- Mọi nút chạm tối thiểu 56 dp; thao tác đạt/không đạt tối đa 3 lần chạm (kiểm bằng đếm thao tác trong kịch bản).
- Giao diện tiếng Việt, ngày giờ theo vi-VN.
- Coverage ≥ 80%, ruff và lint web sạch, OpenAPI cập nhật, plan epic được cập nhật.

## 2. Đánh giá hiện trạng

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phụ thuộc E9 | ⬜ | Chưa có |
| Header `Idempotency-Key`, `X-Device-Id` | ⬜ | Không có trong `apps/api/app` (đã tìm: không có kết quả) |
| Vai trò `FIELD_ENGINEER` | ✅ | `app/core/rbac.py` (E0) |
| Trang web hiện có | ✅ | `apps/web/src/app/page.tsx`, `apps/web/src/lib/api.ts` (E0) |
| Next.js 15, Tailwind v4 | ✅ | `apps/web/package.json` (E0) |
| Mẫu lỗi API | ✅ | Trả 409 và 422 theo mẫu các router E1–E3 |
| PWA (manifest, service worker) | ⬜ | Chưa có |
| Thư viện quét mã | ⬜ | Chưa có. Chọn ở Q2 |

## 3. Phát hiện từ rà soát spec

| ID | Mức | Phát hiện | Xử lý đề xuất |
|---|---|---|---|
| S1 | CAO | CLAUDE.md yêu cầu `Idempotency-Key` và `X-Device-Id` cho mọi lệnh ghi từ thiết bị, nhưng spec không nêu. Chưa có ở API | Áp dụng cho các endpoint được gọi từ PWA. Ghi rõ trong OpenAPI |
| S2 | CAO | Spec yêu cầu "tự động đẩy lên Drive" ngay khi chụp, nhưng E5 chỉ làm một chiều và chưa có đẩy file | Lưu cục bộ trước, đẩy Drive sau khi E5 xong (Q3) |
| S3 | TB | Spec không nói ảnh có GPS lấy từ đâu: EXIF hay vị trí của trình duyệt. Hai nguồn khác nhau | Lưu cả hai, EXIF là nguồn chính (Q4) |
| S4 | TB | Spec nói "quét mã vạch/QR"; chưa rõ quét bằng camera hay nhập tay khi không quét được | Hỗ trợ cả hai, nhập tay là dự phòng |
| S5 | THẤP | Spec ghi "Mobile Web" và "PWA" nhưng không nêu yêu cầu cài đặt. Trình duyệt iOS có giới hạn về service worker và camera | Kiểm trên Safari iOS (Q6) |

## 4. Phụ thuộc và rủi ro dữ liệu

| Phụ thuộc | Nội dung | Ảnh hưởng |
|---|---|---|
| E9 | Serial, ma trận giao, biên bản | Không có E9 thì màn hình không có dữ liệu |
| E5 | Đẩy file lên Drive | Chỉ ảnh hưởng đến bước đẩy, có thể làm sau |
| Trình duyệt | Camera, GPS, IndexedDB, service worker | iOS Safari hạn chế hơn Android Chrome |
| Thiết bị hiện trường | Mạng yếu, pin yếu | Hàng đợi offline bắt buộc |

## 5. Giả định đang áp dụng (đổi được)

| # | Giả định | Nếu đổi |
|---|---|---|
| G1 | `Idempotency-Key` là UUID do thiết bị tạo khi bắt đầu thao tác. Khóa lưu 7 ngày | Đổi thời hạn trong cấu hình |
| G2 | Mỗi thiết bị có `X-Device-Id` sinh một lần, lưu trong `localStorage` | Dùng định danh khác nếu có yêu cầu |
| G3 | Xung đột được phát hiện bằng số phiên bản (`version`) của bản ghi | Dùng thời gian sửa nếu không thêm được cột `version` |
| G4 | Ảnh lưu trên ổ cục bộ của máy chủ, thư mục theo dự án và ngày | Chuyển sang lưu đối tượng khi triển khai thật |
| G5 | Ghi thời gian bằng UTC, hiển thị theo giờ Việt Nam | Theo CLAUDE.md |

Cấu trúc đề xuất `idempotency_keys` (chờ Q1): `key` (UUID, khóa chính kết hợp `device_id`), `device_id`, `endpoint`, `request_hash`, `status_code`, `response_body` (JSONB), `created_at`. Cùng khóa với khác `request_hash` thì trả 422.

## 6. Quyết định cần người dùng chốt

| # | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| Q1 | Xác nhận cấu trúc `idempotency_keys` ở mục 5? | Đồng ý, lưu kết quả đầu tiên để trả lại khi gửi lại | 🟡 Đã làm theo mặc định, chờ xác nhận |
| Q2 | Quét mã bằng thư viện nào? | API `BarcodeDetector` của trình duyệt nếu có, dự phòng bằng thư viện JavaScript nhẹ có giấy phép permissive. Nhập tay luôn có | ⏸ Chờ xác nhận |
| Q3 | Ảnh lưu cục bộ trước rồi đẩy Drive sau có được không? | Có. Đánh dấu "chờ đẩy" đến khi E5 xong | ⏸ Chờ xác nhận |
| Q4 | GPS lấy từ EXIF hay trình duyệt? | Ưu tiên EXIF. Nếu không có, dùng vị trí trình duyệt và ghi nguồn | ⏸ Chờ xác nhận |
| Q5 | Số phiên bản xung đột đặt ở bảng nào? | Thêm cột `version` vào `delivery_handovers` và `equipment_serials` (migration của E10) | ⏸ Chờ xác nhận |
| Q6 | Kiểm trên thiết bị nào? | Tối thiểu một Android và một iPhone thật, cộng giả lập | ⏸ Chờ người dùng |

## 7. Kế hoạch thực hiện

Quy ước: mỗi việc viết test trước (đỏ), rồi sửa mã (xanh), rồi refactor.

### Pha 0: Chuẩn bị và baseline
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Nhánh `feat/e10-field-pwa` từ `main` | ⬜ | |
| 0.2 | Baseline test API và web (lint, test, build) | ⬜ | |

### Pha 1: Idempotency và xung đột (API, integration)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: cùng khóa, cùng nội dung trả đúng kết quả cũ, không tạo dòng mới | ⬜ | |
| 1.2 | Test đỏ: cùng khóa, khác nội dung trả 422 | ⬜ | |
| 1.3 | Test đỏ: hai thiết bị sửa cùng bản ghi, thiết bị sau nhận 409 kèm trạng thái hiện tại | ⬜ | |
| 1.4 | Model `IdempotencyKey`, migration, thêm `version` (Q5) | ⬜ | |
| 1.5 | Dependency `field_write` đọc header, kiểm tra, lưu kết quả | ✅ | `get_field_write_headers` trong `deps.py`; router commit, service không commit |
| 1.6 | `app/services/field_sync.py` | ⬜ | |

### Pha 2: Ảnh và GPS
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Test đỏ: đổi đuôi file (không phải ảnh) bị từ chối; vượt giới hạn bị từ chối | ✅ | `tests/unit/test_field_rules.py` (chữ ký nhị phân); `..._rejects_text_renamed_to_jpg`; `..._rejected_with_413` |
| 2.2 | Test đỏ: EXIF GPS đọc đúng, thiếu EXIF trả `None` | ⬜ | |
| 2.3 | `app/core/exif_gps.py`, `app/services/field_photos.py` | ✅ | `app/core/exif_gps.py`, `app/core/field_rules.py`, `app/services/field_photos.py`. Giới hạn `MAX_PHOTO_BYTES` là hằng số |
| 2.4 | Endpoint tải ảnh, kiểm quyền theo dự án | ⬜ | |

### Pha 3: PWA và hàng đợi offline (web)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Test đỏ (Vitest): hàng đợi giữ thao tác khi offline, gửi lại đúng một lần | ✅ | `field-queue.test.ts` (8), `field-sender.test.ts` (5), `device-id.test.ts` (3) |
| 3.2 | `apps/web/src/lib/field-queue.ts` (IndexedDB, mọi truy cập có try/catch) | ⬜ | |
| 3.3 | Manifest, service worker, icon | ⬜ | |
| 3.4 | Trang `/field/[projectId]`: chọn cụm, chọn trường, danh sách serial | ⬜ | |
| 3.5 | Quét QR với nhập tay dự phòng | ⬜ | Chưa làm quét QR/BarcodeDetector (Q2). Chưa có nhập tay serial |
| 3.6 | Chụp ảnh và biên bản ký, kiểm nút 56 dp và ≤ 3 lần chạm | ⬜ | |

### Pha 4: Kiểm chứng và đóng việc
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Kịch bản mất mạng và bật lại trên thiết bị thật (Q6) | ⬜ | |
| 4.2 | Ruff, pytest --cov ≥ 80%, lint, test, build web | ⬜ | |
| 4.3 | Kiểm bảo mật: header không tin cậy vô điều kiện, không lưu PII trong IndexedDB, quyền ảnh | 🟡 | Đã có: UUID cho Idempotency-Key, kiểm X-Device-Id, chữ ký ảnh, giới hạn kích thước, tên tệp do máy chủ sinh. Còn: token lưu sessionStorage tạm thời (chưa có đăng nhập web); chưa có endpoint tải ảnh có kiểm quyền |
| 4.4 | Cập nhật `pmis-epics.plan.md` và file plan này | ⬜ | |

## 8. Trạng thái theo yêu cầu

| Yêu cầu | Hiện tại | Đích E10 | Pha |
|---|---|---|---|
| Idempotency và X-Device-Id | ⬜ | ✅ | 1 |
| Xung đột 409 | ⬜ | ✅ | 1 |
| Ảnh có GPS | ⬜ | ✅ | 2 |
| Hàng đợi offline | ⬜ | ✅ | 3 |
| PWA trên iOS và Android | ⬜ | ✅ | 4 |
| Nút 56 dp, ≤ 3 lần chạm | ⬜ | ✅ | 3 |

## 9. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Gửi trùng lệnh ghi khi mạng chập chờn | Idempotency ở API, test gửi lại |
| CAO | Ghi đè dữ liệu của người khác khi hai máy cùng sửa | Số phiên bản và 409, không ghi đè |
| TB | iOS Safari hạn chế camera và service worker | Kiểm trên iPhone thật (Q6), có phương án nhập tay |
| TB | Ảnh chứa thông tin cá nhân, lưu trái phép | Quyền theo dự án, không lưu ảnh trong IndexedDB quá lâu |
| TB | Pin và mạng yếu làm hàng đợi lớn | Giới hạn số thao tác chờ, báo cho người dùng |

## 10. Nhật ký thực hiện

| Ngày | Ghi chú |
|---|---|
| 2026-10-31 | Lập plan từ spec §5.5, CLAUDE.md (quy ước thiết bị hiện trường). Chưa viết mã |
| 2026-11-01 | Làm theo TDD với mặc định đề xuất cho Q1–Q5 (chưa có xác nhận chính thức). Q6 chưa thực hiện. Pillow 11.3.0 được thêm vào `pyproject.toml`. Chưa commit |
| 2026-11-01 | Lệch so với plan: chữ ký biên bản và ảnh lưu trong `site_photos` (JSONB) thay vì `signed_scan_drive_id` (FK tới `drive_files`, cần E5). Ảnh không tăng `version` (chỉ thêm, không xung đột). Chưa thực thi TTL 7 ngày của khóa idempotency (G1); cần job dọn dẹp |

## Acceptance

- [x] Plan đã ghi ra file
- [ ] Q1–Q6 đã được chốt
- [ ] E10 đạt đủ điều kiện "E10 hoàn thành" ở mục 1
