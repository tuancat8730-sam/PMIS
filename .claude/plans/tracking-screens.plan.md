# Plan: Màn hình tracking dự án (tiến độ, kế hoạch, rủi ro, pháp lý, file)

**Nguồn mẫu:** `/Volumes/DATA/project/SGD-HCM/Bao_Cao_Tong_Hop_Du_An_SGD_TPHCM.xlsx` (5 sheet)
**Dữ liệu:** Google Drive, hai dự án: SGD-HCM (`1Os76jS_2CYoU2ZV-OCmBunsjy82PMMsk`) và SGD-Lâm Đồng (`1pVkbl53UdVlzbIkUAAsnnjUruTWdLuNi`). Bỏ qua file ghi âm và video.
**Độ phức tạp:** Large (L)
**Ngày lập:** 2026-11-02

## Quyết định đã xác nhận

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Phạm vi | 5 pha, mỗi pha merge riêng |
| 2 | Schema | Đồng ý thêm cột (milestones, risk_issues) và bảng mới (`project_file_register`, `project_legal_decisions`) |
| 3 | Dữ liệu | Đọc toàn bộ Drive hai dự án, seed cả hai dự án từ dữ liệu tìm được |
| 4 | Xuất file | Chỉ hiển thị trên web. Xuất `.xlsx` để sau |
| 5 | Bắt đầu | Ghi plan thành file md, cập nhật tiến độ, bắt đầu Pha 0 |
| 6 | Media | Bỏ qua m4a, mp4 |
| 7 | Thứ tự đọc (lượt 3) | Ưu tiên Lâm Đồng, sau đó HCM |

## Phạm vi màn hình (theo sheet Excel)

| Sheet | Màn hình | Route web | Nguồn API hiện có |
|---|---|---|---|
| 1. Thông tin chung | Tổng quan dự án | `/projects/[id]/overview` | `projects`, `contracts` + bảng mới `project_legal_decisions` |
| 2. Tiến độ & Nghiệm thu | Kế hoạch và tiến độ | `/projects/[id]/schedule` | `milestones` + cột mới |
| 3. Quản lý rủi ro | Rủi ro | `/projects/[id]/risks` | `risk_issues` + cột mới |
| 4. Hồ sơ pháp lý | Hồ sơ pháp lý | `/projects/[id]/legal` | `legal_documents`, `legal_documents/summary` |
| 5. File & bằng chứng | Quản lý file | `/projects/[id]/files` | `drive/files` + bảng mới `project_file_register` |

## Thiếu dữ liệu và trường

| Mục | Thiếu |
|---|---|
| Rủi ro | `impact`, `likelihood`, `coordinating_units` |
| Mốc | `deliverables`, `acceptance_conditions`, `tvgs_checkpoint`, `pm_comment` |
| Dự án | Số quyết định (phê duyệt dự án, KHLCNT, BCKTKT), nguồn vốn, thời gian thực hiện (bảng `project_legal_decisions`) |
| File | `project_file_register`: mục đích, tình trạng pháp lý, bảo mật/sở hữu, hành động tiếp theo |

## Pattern cần bám theo

| Hạng mục | Nguồn |
|---|---|
| API router | `apps/api/app/api/v1/risk_issues.py`, `milestones.py` |
| Schema | `apps/api/app/schemas/risk_issues.py` (`RequestModel`, `Out` với `from_attributes`) |
| Web data | `apps/web/src/lib/command-center.ts` (hàm fetch có kiểu, `fetchImpl` để test) |
| Web UI | `apps/web/src/components/command-center/command-center-view.tsx` |
| Test | `tests/integration/test_command_center_api.py`, `command-center-view.test.tsx`, `e2e/command-center.spec.ts` |

## Pha

### Pha 0: Đọc Drive và lập bảng ánh xạ dữ liệu
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 0.1 | Ghi plan này thành file md | ✅ | File này |
| 0.2 | Đọc toàn bộ thư mục gốc và thư mục con của SGD-HCM (bỏ media) | 🟡 | Đã liệt kê gốc và 4 thư mục con. Đã đọc: Báo cáo giám sát tuần 02 (TVGS Crystal). Chưa đọc: nội dung `Tai lieu nha thau` (có `nhat_ky_thi_cong`, `BienBanKhaoSat-LHP-10-28-2026`), `Tài Liệu Lưu trữ` (có `Nhà Thầu`, `Giám Sát`, `V3 BCKTKT` 5 MB), `Báo cáo tuần` (có `TVGS`, `nhà thầu`, `20261002`, `20261008`, `20261023`, `20261030`), `MeetingWeekly` |
| 0.3 | Đọc toàn bộ thư mục gốc và thư mục con của SGD-Lâm Đồng (bỏ media) | 🟡 | Đã đọc: Chỉ mục hồ sơ, Phụ lục tiến độ, Báo cáo tuần QLDA lần 1 tuần 03, Văn bản hợp đồng (trang ký), BB thương thảo (thẩm định, gói khác), Hợp đồng TVGS, QĐ chỉ định TVGS 3505, Tờ trình 2710/TTr-ALT, Công văn gửi trường (pdf), Đề cương TVQLDA (docx), Đề cương TVGS trình duyệt (công văn 1910/SGM), QĐ phê duyệt Đề cương TVGS (dự thảo), Phụ lục danh mục thiết bị (docx), Serial 320 bộ (xlsx), Kế hoạch bố trí xe (xlsx), Triển khai giao nhận (pdf), Công văn gửi trường (docx), họp triển khai 21.10 (rỗng), hop DACX 03 23.10 (ghi chú ngắn). Chưa đọc: Đề cương TVGS (docx, 462 KB), Ke_hoach_trien_khai (docx, 227 KB), Biên bản bàn giao từng trường (4 cụm, nhiều file), Phụ lục bảng giá / Điều kiện cụ thể / Ủy quyền (pdf), Công văn mời họp (docx, pdf), Ra soát lần 3 (xlsx 3 MB): đã đọc qua script, xem lượt 5. Giám sát trực tiếp là ảnh, chưa xử lý |
| 0.4 | Đối chiếu: HCM lấy từ Excel mẫu (mốc, rủi ro, pháp lý, file); LD lấy từ tài liệu Drive | 🟡 | HCM: Excel đã đọc đủ 5 sheet. LD: xem bảng bên dưới |
| 0.5 | Lập bảng ánh xạ: file nguồn → bảng/cột đích, kèm thiếu sót | 🟡 | Bản nháp cho LD bên dưới, lượt 3 đã bổ sung |
| 0.6 | Chốt danh sách dữ liệu có đủ nguồn để seed, và dữ liệu thiếu | 🟡 | Đã chốt nguồn cho milestones LD (Phụ lục danh mục + Kế hoạch phối hợp), milestones HCM (Excel + biên bản giao ban), risk LD (báo cáo tuần), risk HCM (Excel + báo cáo TVGS). Chưa mở các file lẻ: biên bản bàn giao từng trường LD (61 thư mục, tổng 4 cụm, chỉ đếm), 3 nhật ký thi công HCM, 6 biểu mẫu nghiệp vụ, 11 file TTHC, 3 file phần mềm, 2 file nghiệm thu. Phụ lục bảng giá, Điều kiện cụ thể, Ủy quyền LD (pdf) chưa mở |

### Pha 1: Tiến độ & kế hoạch (sheet 2) và rủi ro (sheet 3)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1.1 | Test đỏ: trường mới của milestones và risk_issues | ✅ | `tests/unit/test_risk_matrix_rules.py`, `tests/integration/test_tracking_fields_api.py`. Đỏ trước (module thiếu), xanh sau khi làm |
| 1.2 | Migration cột mới (nullable) và round-trip | ✅ | Migration `a1c4e8f2b9d3`: milestones (deliverables, acceptance_conditions, tvgs_checkpoint, pm_comment), risk_issues (impact, likelihood, coordinating_units, enum `risk_level`). Đã `make api-migrate` trên DB dev (được duyệt), round-trip downgrade/upgrade OK, `alembic check` sạch |
| 1.3 | API: schema mở rộng; `GET /projects/{id}/schedule-matrix`; `GET /projects/{id}/risk-matrix` | ✅ | `app/api/v1/tracking.py`, `app/services/tracking_matrix.py`, `app/schemas/tracking.py`, `app/core/risk_matrix_rules.py`. Điểm rủi ro = thứ hạng tác động × khả năng (1–16). Full suite 527 passed, ruff sạch |
| 1.4 | Web: `/projects/[id]/schedule` và `/projects/[id]/risks` | ✅ | `src/lib/tracking.ts`, `src/components/tracking/` (bảng, khung `matrix-page.tsx`), 2 trang trong `src/app/projects/[projectId]/`. Test vitest 53 passed, tsc và eslint sạch, `next build` biên dịch được 2 route |
| 1.5 | Seed mốc và rủi ro cho hai dự án | ✅ | `app/db/seed_data/{hcm,lam_dong}_{milestones,risks}.json`, build HCM từ Excel sheet 2 và 3. LD: 5 mốc và 8 rủi ro từ báo cáo tuần và Ra soát (không có mức tác động/khả năng trong nguồn, để trống). `make seed-projects` đã chạy: HCM +12 rủi ro +7 mốc, LD +5 mốc +8 rủi ro. HCM M1, M8, M9 (bản seed cũ) đã được làm mới từ Excel: tên, sản phẩm bàn giao, điều kiện nghiệm thu, mốc TVGS, ghi chú PM. Ngày gốc và ngày bù không đổi, đã đối chiếu với Excel. Seed chỉ ghi đè các trường chữ nguồn, không đụng trạng thái, tiến độ, ngày thực tế. Đã chạy `make seed-projects` trên DB dev và kiểm tra |

### Pha 2: Hồ sơ pháp lý (sheet 4)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 2.1 | Kiểm `legal_documents` đủ trường; thêm nếu thiếu | ⬜ | |
| 2.2 | Web: `/projects/[id]/legal`, nhóm theo giai đoạn | ⬜ | |
| 2.3 | Seed đầu mục pháp lý cho hai dự án | ⬜ | |

### Pha 3: Quản lý file & bằng chứng (sheet 5)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 3.1 | Migration `project_file_register` | ⬜ | |
| 3.2 | API đọc và ghi register; liên kết với `drive_files` | ⬜ | |
| 3.3 | Web: `/projects/[id]/files` | ⬜ | |

### Pha 4: Tổng quan dự án (sheet 1)
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 4.1 | Migration `project_legal_decisions` | ⬜ | |
| 4.2 | Web: `/projects/[id]/overview`, hiển thị TMĐT, nguồn vốn, ma trận hợp đồng | ⬜ | |

### Pha 5: Seed và kiểm chứng
| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 5.1 | Seed SGD-HCM và SGD-LD theo bảng ánh xạ | ⬜ | |
| 5.2 | pytest (unit, integration), vitest, Playwright cho từng trang | ⬜ | |
| 5.3 | ruff, `alembic check`, chạy seed hai lần | ⬜ | |

## Bảng ánh xạ (Pha 0)

### Dự án SGD-Lâm Đồng (bản nháp)

| Nguồn Drive | Đích | Dữ liệu rút ra |
|---|---|---|
| Chỉ mục hồ sơ Gói thầu LD.xlsx (35 dòng) | `legal_documents` (LD) | Mã file, tên văn bản, ngày ban hành, căn cứ, đơn vị lập và phối hợp, ghi chú. Nhiều dòng "Chưa có file" |
| Chỉ mục hồ sơ, mục 05 và 13–19, 22–29 | `milestones` (LD) | Triển khai 14/10/2026–05/02/2027. Đợt 1 Tin học: kiểm tra 26/10–05/11, bàn giao 27/10–10/11. Đợt 2 Ngoại ngữ: kiểm tra 10/11–15/11, bàn giao 20/11–25/11. Đợt 3 các môn còn lại: kiểm tra 06/12–30/12, bàn giao 15/12–15/01/2027. Nghiệm thu tổng thể 05/02/2027. Thanh lý HĐ thi công 08/02/2027 |
| Chỉ mục hồ sơ, mục 22–25 | `milestones` (LD), TVGS | Báo cáo giám sát và nghiệm thu TVGS 08/02/2027. HĐ TVGS 120 ngày từ 12/10/2026 |
| Phụ lục tiến độ LD.pdf (219 hạng mục) | `contracts` (điều khoản thời gian) | Mọi hạng mục giao trong ≤120 ngày từ hiệu lực 09/10/2026, hết hạn 06/02/2027. Không có ngày riêng từng hạng mục |
| Phụ lục danh mục thiết bị giao theo đợt (docx) | `milestones` (LD) | 62 đơn vị, mỗi đơn vị có ngày giao Đợt 1, 2, 3 và số mặt hàng. Nguồn chính cho milestones LD. Dòng 48 (THPT Phan Thiết) không có thiết bị |
| Báo cáo tuần QLDA lần 1 tuần 03 (docx) | `milestones` (trạng thái), `risk_issues` (LD), `legal_documents` | Tiến độ 20/120 ngày đến 28/10. Đợt 1: 9/60 theo lịch, 25/60 trong tuần. Đợt 2 0/37, Đợt 3 0/61. Nghiệm thu tổng thể 16/12/2026–28/01/2027. Có danh sách vấn đề cần CĐT chỉ đạo (4 nội dung) |
| Văn bản hợp đồng (pdf, trang ký) | `contracts`, `projects` | Hợp đồng HD2600226555_2609110905 ký 06/10/2026, hiệu lực 09/10/2026, giá 106.225.000.000 đ, trọn gói. Liên danh Nguyên Luân đứng đầu gồm Nguyên Luân, Crystal, Đức Mai Khôi, Liên Thành Phát |
| Hợp đồng TVGS LD (docx) | `contracts` | Sài Gòn Mới, 80/2026/HĐTV, 360.000.000 đ, 120 ngày, tạm ứng 30% (108 triệu), thanh toán 2 lần (50% và 50%) |
| QĐ 3505 chỉ định TVGS (pdf) | `project_legal_decisions` | Số 3505/QĐ-SGDĐT, 08/10/2026. Chỉ định rút gọn. Điều chỉnh thời gian LCNT theo QĐ 3498 cùng ngày |
| Đề cương TVQLDA (docx) | `milestones` (quy trình), `project_legal_decisions` | An Lập Thịnh, 405 triệu, 180 ngày, mốc N → N+7 (hồ sơ) và N → N+10 (đề cương). Giám đốc QLDA Nguyễn Minh Nhựt |
| Dự toán và KHLCNT (QĐ 2065, trích từ đề cương) | `projects` (TMĐT), `contracts` (gói) | Dự toán 125.230.620.500 đ, gồm thiết bị 112.437.510.500 đ, dự phòng 11.394.353.000 đ. 5 gói trong KHLCNT |
| Serial 320 bộ PC FPT Elead (xlsx) | `project_file_register` (LD, bằng chứng) | 320 dòng gồm S/N thùng PC và S/N LCD. Khớp báo cáo tuần |
| Kế hoạch bố trí xe Tổ nghiệm thu (xlsx) | `milestones` (nghiệm thu), `project_file_register` | 4 tổ, 13 chuyến, 69 ngày xe, 61 đơn vị. Lịch đề xuất 04/01/2027–29/01/2027. Xong trước Tết Đinh Mùi (06/02/2027) |
| Công văn triển khai giao nhận (pdf, docx) và Tờ trình 2710 | `milestones`, `project_legal_decisions` | Kế hoạch giao 3 đợt, đào tạo và nghiệm thu từ 16/12/2026–28/01/2027. Đơn vị phản hồi trước 29/10/2026 |
| HĐ LD (đã seed) | `contracts`, `projects` | Đã có trong DB |
| DS 62 trường (đã seed) | `beneficiary_units` | Đã có trong DB |
| Excel mẫu HCM | `milestones`, `risk_issues`, `legal_documents`, `project_file_register` của HCM | Sẵn, đã đọc |

**Mâu thuẫn trong nguồn LD, cần ghi nhận:**
- Phụ lục tiến độ / KH ghi HĐ ký 09/10, HĐ ghi 06/10 (09/10 là ngày hiệu lực).
- Đề cương TVGS ngày 13/10 trước KH triển khai 16/10.
- Đợt 3 giao từ 15/12 nhưng kiểm tra đến 30/12.
- Trường THPT Phan Thiết (STT 62 trong Kế hoạch xe, STT 48 trong Phụ lục danh mục) thiếu thiết bị trong biên bản Đợt 3. Đánh số đơn vị khác nhau giữa hai file.
- Đợt 2 (Ngoại ngữ): Công văn gửi trường (pdf và docx) và Tờ trình ghi 16/11. Báo cáo tuần và Phụ lục danh mục ghi 20/11 hoặc 20/11–25/11. Mốc 16/11 lệch so với Phụ lục và Báo cáo tuần.
- Tờ trình: số `2710/TTr-ALT`, ngày 27/10/2026. Báo cáo tuần ghi `Tờ trình số 2610/TTr-ALT ngày 26/10/2026`. Số và ngày không khớp.
- Công văn gửi trường: bản pdf đề số `5776/QĐ-SGDĐT` (tiêu đề "Công văn" nhưng số dạng quyết định), ngày 28/10. Bản docx để trống số, ngày 27/10. Số và ngày không khớp giữa hai bản.
- Đề cương TVGS `1310/ĐC-TVGS-SGM` (13/10): Báo cáo tuần ghi TVQLDA trình bằng `1910/CV-ALT` (19/10). Công văn thật sự ngày 19/10 là `1910/SGM-GSV` của Sài Gòn Mới trình. Người trình không khớp.
- QĐ phê duyệt Đề cương TVGS (docx): số để trống, ngày 20/10, Giám sát trưởng Phạm Ninh Hà. Báo cáo tuần ghi dự thảo, khớp.
- Hợp đồng TVGS LD: ngày ký để trống. Dùng ngày QĐ 3505 (08/10) làm mốc tạm.
- BB thương thảo "thẩm định E-HSMT" (21/10/2026, Sài Gòn Mới, 45 triệu, 30 ngày) thuộc gói bàn ghế và thiết bị điện tử mua sắm tập trung, không thuộc gói lớp 10. Gói thẩm định của dự án LD trong KHLCNT là 115 triệu. Cần xác nhận có đưa vào dự án LD không.
- Danh bạ TVQLDA: Báo cáo tuần ký "Nguyễn Minh Nhựt, Giám đốc QLDA". Công văn pdf ghi TVQLDA có "Giám đốc Nguyễn Bích Ngọc, 09 Lương Thế Vinh". Cần xác nhận người đại diện.
- Quyết định thành lập Tổ nghiệm thu: Báo cáo tuần ghi dự thảo. Kế hoạch xe ghi "QĐ số 3748/QĐ-SGDĐT ngày 28/10/2026". Cần xác nhận số 3748 đã ban hành.
- Số HĐ TVGS: Chỉ mục ghi `80/2026/HĐTV/SDGĐTLĐ-SGM` (đúng với hợp đồng LD). Excel HCM ghi `24.8.26/HĐTV/SGDĐT-CRYSTAL` (HCM, không xung đột).
- Serial: báo cáo tuần ghi 320/1.420 bộ, Drive có 320 bộ. Thiếu 1.100 bộ là thiếu thật.
- File `họp triển khai 21.10.txt` rỗng (0 ký tự).
- Dự án LD dùng TMĐT tạm. Dự toán 125.230.620.500 đ (QĐ 2065) thay cho giá gói thầu. TMĐT chính thức trong QĐ 2891 chưa đọc.

**Dữ liệu HCM rút ra thêm (từ Báo cáo giám sát tuần 02 của TVGS Crystal, 02–07/10/2026):**
- Gói triển khai: Hợp đồng 29/HĐKT-DVN ký 21/09/2026 với Liên danh DVN, 4.848.186.000 đ, 120 ngày. Tiến độ 17/120 ngày đến 07/10.
- Hợp đồng TVGS Crystal: 24.8.26/HĐTV ký 24/08/2026, 150 ngày, kết thúc 21/01/2027.
- Mốc H2 (SRS, 07/10/2026) không đạt. H3 phê duyệt thiết kế 13/10/2026. H6 kế hoạch kiểm thử 08–13/10.
- Rủi ro R01–R14 có mức độ, lấy thẳng từ báo cáo. R05 ATTT cấp độ 3 "Rất cao". R02 tiến độ gắt "Rất cao".

**Lượt 5: Ra soát lần 3 (LD, xlsx 3,3 MB, đã đọc bằng script):**
- Tải qua Drive, giải mã base64 và đọc XML bằng thư viện chuẩn (không có openpyxl). Script và file trung gian nằm trong scratchpad (`xlsx_read.py`, `summarize_sheets.py`, `school_summary.json`). Đã tổng hợp 62 sheet đơn vị và sheet `Danh sách`. Sheet `SGV`, `foxz`, `Sheet1` rỗng. Các sheet `LOP 10`, `LOP 10 (2)`, `LOP 10 (9)` là biểu mẫu nền, chưa kiểm tra chi tiết.
- Sheet `Danh sách` là sổ theo dõi tình trạng nhập và hồ sơ của 62 đơn vị. 7 đơn vị ghi "Chưa có bản đóng dấu" (1.3, 1.6, 2.18, 5.3, 5.4, 5.6, 5.7). Phan Thiết (5.10) ghi "không có nhu cầu". 3 đơn vị chưa có tình trạng (5.24, 6.1, 6.2).
- 62 sheet đơn vị (mẫu Biểu mẫu số 01, Đăng ký thiết bị dạy học tối thiểu). Mỗi sheet có số HS lớp 10 và ~394 mục thiết bị, với định mức, hiện trạng, nhu cầu, và hai cột đăng ký "Lần 3" và "Lần 1".
- Tổng toàn bộ 62 sheet (cộng số lượng khác đơn vị, chỉ để so sánh xu hướng): đăng ký Lần 1 = 128.518, Lần 3 = 81.841, nhu cầu = 190.381. 55 đơn vị có Lần 3 thấp hơn Lần 1.
- Chất lượng dữ liệu: 61/62 sheet còn tên trường là placeholder `TRƯỜNG…`. Tên đơn vị phải lấy từ `Danh sách`. 8 đơn vị ghi HS lớp 10 = 35 (1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 2.12). Có thể là giá trị mặc định chưa cập nhật, cần xác nhận. Tổng HS 25.553.
- Mâu thuẫn: số mục nhu cầu của từng đơn vị không đồng nhất với PL danh mục giao hàng (mỗi đơn vị có số mặt hàng khác). Cần xác nhận nguồn nào là chuẩn trước khi seed `milestones`.

**Lượt 4 (đã đọc), Lâm Đồng và HCM:**
- Đề cương TVGS LD (docx, 113 KB, đọc qua trích xuất): T0 = 09/10/2026. Lịch giám sát theo 14 đầu việc, khớp Công văn trường (Đợt 2 giao 16/11–25/11). Hợp đồng Nguyên Luân: 219 hàng hóa, thanh toán 4 đợt, tạm ứng thu hồi 31.867.500.000 đ (30%). Đợt 1 thu hồi tối thiểu 10 tỷ, đợt 2 lũy kế tối thiểu 20 tỷ, đợt 3 thu hồi hết trước 31/12/2026.
- Phụ lục tiến độ hợp đồng (Kế hoạch phối hợp, docx): 62 đơn vị, mỗi đơn vị có ngày giao, lắp đặt và nghiệm thu từng đợt. Đây là nguồn chi tiết cho `milestones` LD. Dòng này lệch đánh số 1 đến 2 với Phụ lục danh mục.
- Mời họp triển khai (1910/CV-ALT, 19/10): họp 21/10 tại Sở. Ký bởi Nguyễn Bích Ngọc, Giám đốc An Lập Thịnh. Điều này khớp với danh bạ mâu thuẫn ở trên (Nhựt là Giám đốc QLDA, Ngọc là Giám đốc công ty).
- Thỏa thuận liên danh 14/07/2026; Giấy ủy quyền 01/2026/GUQ-LD ngày 11/09/2026 (trích từ Văn bản hợp đồng).

**Dữ liệu HCM rút ra (lượt 4):**
- Báo cáo kinh tế kỹ thuật (BCKTKT, docx 5 MB, đã đọc qua trích xuất): ngày 06/02/2026. Thẩm định theo công văn SKHCN 1070/SKHCN-CĐS (06/02/2026). TMĐT dự kiến 6.000.000.000 đ, nguồn NSNN chi đầu tư phát triển. Tổng số trường 1.670, theo BCKTKT. Mâu thuẫn trong chính BCKTKT: "Thời gian thực hiện: Năm 2026" nhưng đoạn khác ghi triển khai từ 2025 đến quý III/2026. Hợp đồng gói triển khai là 4.848.186.000 đ, thấp hơn TMĐT.
- Nhà thầu DVN (Liên danh DVN): Hợp đồng 29/HĐKT-DVN, 21/09/2026, 120 ngày. Báo cáo tiến độ tuần 1 (25/09–01/10), tuần 2 (02–07/10), tuần 3 (09–15/10), tuần 4 (16–22/10). Mốc "Hoàn thành khảo sát và xác nhận yêu cầu" chậm 16 ngày ở tuần 4. Phê duyệt thiết kế 13/10 chưa đạt, còn đang thực hiện.
- Biên bản giao ban (TVGS, QLDA, nhà thầu): 02/10, 08/10, 23/10, 30/10/2026. Điểm chính: 30/10 đề xuất rút khảo sát từ 6 trường xuống 3 trường thí điểm (Tiểu học, THCS, THPT). Nghiệm thu kỹ thuật phần mềm trước 30/11/2026. Quyết toán dự án trước 30/12/2026. Trường THPT Chuyên Lê Hồng Phong đã khảo sát.
- Mâu thuẫn HCM: số trường khảo sát ghi 6 trường và 2 UBND (23/10, nhà thầu tuần 4), 9 trường (02/10, "3 cấp học × 3 khu vực"), 3 trường thí điểm (30/10). Số trường cần đại diện: TVGS ghi >2.000, BCKTKT ghi 1.670.
- Mâu thuẫn HCM: công văn Sở gửi trường: 22/10 (biên bản 23/10 và báo cáo tuần 4), nhưng biên bản 08/10 nói chưa có biểu mẫu và báo cáo tuần 2 nói dự thảo công văn gửi 21/10. Ngày và trạng thái công văn chưa khớp.
- Mâu thuẫn HCM: quy tắc mã định danh thiết bị dành 2 ký tự cho số thứ tự, không đủ khi quá 99 thiết bị (báo cáo tuần 3). Nhà thầu đề xuất tăng lên 4 ký tự. Đang chờ CĐT.
- File `Ra soát lần 3` (xlsx 3 MB): đã đọc qua script (xem lượt 5).

**Còn lại trong Pha 0:**
- LD: Biên bản bàn giao từng trường (4 cụm, nhiều file), Phụ lục bảng giá / Điều kiện cụ thể / Ủy quyền (pdf).
- HCM đã đọc: 4 báo cáo tuần của nhà thầu DVN (`Báo cáo tuần/nhà thầu`), 4 biên bản giao ban (02/10, 08/10, 23/10, 30/10), BCKTKT. Chưa mở: `nhat_ky_thi_cong` (trong Tai lieu nha thau), `BienBanKhaoSat-LHP-10-28-2026` (trong Tai lieu nha thau), `Nhà Thầu` và `Giám Sát` (trong Tài Liệu Lưu trữ), `TVGS` (trong Báo cáo tuần; đã đọc báo cáo tuần 02), và các thư mục con của `Nhà Thầu` (Thủ tục hành chính, Nghiệp vụ, Phần mềm, Nghiệm thu, Quản lý dự án). Video MeetingWeekly bỏ qua theo quy định media.
- HCM: toàn bộ nội dung các thư mục con (xem 0.2).

## Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Đọc toàn bộ Drive tốn nhiều lượt; file PDF lớn | Đọc theo từng file, lưu kết quả trung gian vào scratchpad, không đọc lại |
| CAO | Nhập tay dữ liệu dễ sai số | Seed từ file nguồn, đối chiếu từng dòng |
| CAO | Migration thêm cột vào bảng có dữ liệu | Cột nullable, round-trip migration |
| TB | Dữ liệu LD có thể không đầy đủ như HCM | Hiển thị trạng thái trống, ghi rõ trong bảng ánh xạ |
| TB | Trang nặng với 89 đầu mục pháp lý | Nhóm theo giai đoạn |

## Nhật ký

| Ngày | Ghi chú |
|---|---|
| 2026-11-02 | Lập plan từ câu trả lời của người dùng. Bắt đầu Pha 0: đã liệt kê thư mục gốc HCM và LD, và 5 thư mục con LD |
| 2026-11-02 | Pha 0 tiếp: đọc Chỉ mục hồ sơ LD và Phụ lục tiến độ LD. Lập bản nháp bảng ánh xạ LD và danh sách mâu thuẫn |
| 2026-11-02 | Pha 0 lượt 2: đọc Báo cáo tuần QLDA LD tuần 03, Văn bản hợp đồng LD, Hợp đồng TVGS LD, Tờ trình 2710, Báo cáo giám sát tuần 02 của HCM. Liệt kê con của LD và HCM |
| 2026-11-02 | Lượt 6 (đọc hết theo cấu trúc, mở tài liệu chính): Đề xuất danh sách khảo sát (14/10: 9 trường + 2 phường), Báo cáo nhanh khảo sát (29/10: danh sách khác 14/10), Biên bản họp khởi động (25/09). Cấu trúc LD: 4 cụm, 61 thư mục đơn vị. Cấu trúc HCM: 96 mục con cấp 1–2. Pha 1: 1.1, 1.3 xong; 1.2 cần `make api-migrate` trên DB dev. Ghi chú: danh sách trường khảo sát HCM đổi giữa 14/10 và 29/10 |
| 2026-11-02 | Lượt 4 và 5: đọc Đề cương TVGS LD, Kế hoạch phối hợp, Công văn mời họp, BCKTKT HCM, 4 báo cáo tuần DVN, 4 biên bản giao ban HCM. Đọc Ra soát lần 3 qua script (tải base64, giải mã, đọc XML bằng thư viện chuẩn) |
| 2026-11-02 | Pha 0 lượt 3 (ưu tiên Lâm Đồng): đọc Phụ lục danh mục thiết bị, Serial 320 bộ, Kế hoạch bố trí xe, QĐ 3505, Đề cương TVQLDA, Đề cương TVGS trình duyệt, QĐ phê duyệt Đề cương TVGS, Công văn gửi trường (pdf và docx), Triển khai giao nhận. Ghi thêm mâu thuẫn và dữ liệu seed. Plan đã được viết lại gọn, bỏ khối trùng. Chưa sửa code, chưa seed |
