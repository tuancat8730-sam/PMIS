# Kế hoạch: cập nhật nội dung tab "Tổng quan" theo báo cáo mẫu

**Nguồn yêu cầu:** ảnh "BÁO CÁO TỔNG QUAN QUẢN LÝ DỰ ÁN (PROJECT OVERVIEW)", cập nhật 02/11/2026, gồm ba mục I, II, III.
**Phạm vi:** trang `/projects/[projectId]/overview` và `OverviewView`.
**Độ phức tạp:** Large (L) nếu đưa dữ liệu vào DB; Medium (M) nếu hiển thị dữ liệu tĩnh.
**Ngày lập:** 2026-11-02
**Trạng thái:** Đã có đáp án cho các câu hỏi, CHỜ XÁC NHẬN plan. Chưa sửa code.

## Yêu cầu hiểu được

Thay nội dung tab "Tổng quan" bằng ba khối như trong báo cáo mẫu:

- **I. Thông tin pháp lý và tổng mức đầu tư gói thầu:** tên dự án, chủ đầu tư, đại diện pháp luật, cơ quan quyết định đầu tư, các quyết định phê duyệt (chủ trương, BCKTKT, KHLCNT, kết quả LCNT), tổng mức, chi phí từng khoản (phần mềm, QLDA, tư vấn, khác và dự phòng), hình thức QLDA, nguồn vốn, thời gian thực hiện, hạn giải ngân.
- **II. Ma trận hợp đồng và các đơn vị thực hiện:** vai trò, đơn vị, số hợp đồng, ngày ký, giá trị, thời hạn, đầu mối/nhân sự chủ chốt, hiện trạng và đánh giá của PM.
- **III. Quy mô kỹ thuật và chỉ tiêu nghiệm thu ràng buộc:** hạng mục kỹ thuật, quy chuẩn, căn cứ pháp lý, mô tả giải pháp, trách nhiệm, tiêu chuẩn nghiệm thu, rủi ro liên quan, trạng thái giám sát.

## Hiện trạng (đã đọc code)

| Thành phần | Hiện có | Ghi chú |
|---|---|---|
| [overview-view.tsx](apps/web/src/components/tracking/overview-view.tsx) | 4 ô: tổng mức, nguồn vốn, thời gian, chủ đầu tư | Hiển thị `approval` là quyết định `PROJECT_APPROVAL` |
| [overview.ts](apps/web/src/lib/overview.ts) | Tải song song project, legal-decisions, contracts | Kiểu `ContractSummaryRow` chỉ có 6 trường |
| [overview/page.tsx](apps/web/src/app/projects/[projectId]/overview/page.tsx) | Dùng `MatrixPage` | |
| [models/project.py](apps/api/app/models/project.py) | Có `decision_authority`, `investor_name`, `total_investment` | |
| Bảng quyết định pháp lý | Có `kind`, số QĐ, ngày, cơ quan, số tiền, nguồn vốn, thời gian | Thiếu cột ngày quyết định của nhiều loại |
| Bảng hợp đồng | Có `package_name`, `package_kind`, số HĐ, ngày ký, hạn, giá trị | Thiếu vai trò, đơn vị thực hiện, đầu mối, hiện trạng |
| Chi phí theo khoản | Không có | Phải thêm dữ liệu mới |
| Quy mô kỹ thuật, tiêu chuẩn nghiệm thu | Không có | Phải thêm dữ liệu mới |

## Khoảng trống so với ảnh

1. **Mục III chưa có nguồn dữ liệu nào.** Đây là phần lớn nhất. Cần bảng mới hoặc chấp nhận nội dung tĩnh.
2. **Mục I, chi phí theo khoản:** ảnh ghi kèm chú thích dạng văn bản ("tiết kiệm ~600 triệu", "Giá trúng HĐ trên khai..."). Cần quyết định tách thành số và ghi chú.
3. **Mục II, cột "Đầu mối" và "Hiện trạng & đánh giá của PM":** là dữ liệu nhập tay, chưa có chỗ lưu.
4. **Một số số liệu trong ảnh có thể lệch với seed trên DB dev.** Phải đối chiếu trước khi hiển thị.
5. **Hai dòng "Chủ đầu tư" và "Tư vấn quản lý" trong mục II không phải hợp đồng thật.** Chủ đầu tư không có số HĐ. Cần quyết định có giữ trong bảng hợp đồng không.

## Quyết định đã chốt (2026-11-02)

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Nguồn dữ liệu | Phương án C (lai): DB cho quyết định, hợp đồng, tổng mức; bảng mới cho chi phí theo khoản, yêu cầu kỹ thuật và phần nhập tay |
| 2 | Mục III | Thêm bảng mới, seed từ ảnh, làm cùng Pha 1 |
| 3 | Trùng tab Quyết định và Hợp đồng | Tổng quan hiển thị đầy đủ như ảnh; hai tab riêng giữ nguyên |
| 4 | Đối chiếu số liệu với DB dev | Có, làm ở Pha 0, không tự chọn giá trị khi lệch |
| 5 | Bố cục điện thoại | Chưa hỏi. Giữ đề xuất: thẻ trên điện thoại, bảng trên máy tính |

## Câu hỏi đã trả lời (giữ để tham chiếu)

1. **Nguồn dữ liệu:**
   - A. Nhúng nội dung ảnh thành dữ liệu tĩnh trong component. Nhanh, nhưng vi phạm quy ước "không hard-code số liệu", và sẽ lệch khi dữ liệu đổi.
   - B. Thêm bảng và seed trên DB (migration mới). Đúng quy ước CLAUDE.md, nhưng làm đổi schema, trong khi plan tracking trước đó đã loại trừ đổi schema.
   - C. Lai: dùng DB cho những gì đã có bảng (quyết định, hợp đồng, tổng mức), thêm bảng mới cho chi phí theo khoản và yêu cầu kỹ thuật, còn phần nhập tay (đầu mối, hiện trạng) lưu trong bảng mới.
   - **Đề xuất: C.**
2. **Mục III:** có cần bảng mới cho hạng mục kỹ thuật và tiêu chuẩn nghiệm thu không, hay tạm bỏ mục này?
3. **Quyết định và Hợp đồng:** tab riêng `/decisions` và `/contracts` đã có. Mục I và II trong ảnh trùng với hai tab đó. Bạn muốn:
   - A. Giữ tab riêng và Tổng quan chỉ hiển thị bản tóm tắt.
   - B. Tổng quan hiển thị đầy đủ như ảnh, còn tab riêng giữ nguyên.
4. **Đối chiếu số liệu:** bạn có muốn tôi đối chiếu ảnh với dữ liệu DB dev và báo lại các chỗ lệch, trước khi nhập không? Tôi đề xuất có.
5. **Bố cục điện thoại:** tôi đề xuất mỗi mục là một khối thẻ, mục II và III trên điện thoại hiển thị thành thẻ theo dòng, máy tính hiển thị bảng. Bạn đồng ý không?

## Mẫu cần bám theo

Sẽ xác định khi bắt đầu thực hiện, dựa trên `matrix-page.tsx`, `legal-table.tsx` và các test trong `components/tracking/`. Các chuỗi đang được e2e dùng (ví dụ "Tổng quan" trong `e2e/command-center.spec.ts`) phải giữ hoặc cập nhật cùng lúc.

## Các bước (nếu chọn phương án C)

### Pha 0: Đối chiếu
| ID | Việc | Trạng thái |
|---|---|---|
| 0.1 | Lập bảng đối chiếu từng ô trong ảnh với DB dev (số tiền, ngày, số QĐ, số HĐ) | ✅ |
| 0.2 | Ghi các chỗ lệch vào mục Nhật ký, không tự chọn giá trị | ✅ |

**Kết quả đối chiếu** (dự án SGD-HCM-CSVC-2026; đọc DB dev, không ghi gì):

| Ô trong ảnh | Ảnh | DB dev | Kết quả |
|---|---|---|---|
| Tên dự án | Xây dựng hệ thống quản lý dữ liệu về CSVC và thiết bị trường học | Khớp | Khớp |
| Chủ đầu tư | Sở GD&ĐT TP.HCM | Khớp | Khớp |
| Cơ quan quyết định đầu tư | Ủy ban nhân dân Thành phố Hồ Chí Minh | `decision_authority` trống | **Thiếu** |
| Tổng mức đầu tư | 5.999.498.939 đ | 5.999.498.939 | Khớp |
| QĐ phê duyệt chủ trương | 1595/QĐ-SGDĐT, 22/05/2026 | Khớp | Khớp |
| QĐ phê duyệt BCKTKT | 1421/QĐ-SGDĐT, 12/05/2026 | Khớp | Khớp |
| QĐ phê duyệt KHLCNT | 1889/QĐ-SGDĐT, 12/06/2026 | Khớp | Khớp |
| QĐ phê duyệt KQLCNT | 4452/QĐ-SGDĐT, 07/09/2026 | Khớp (ngày và số) | Khớp; ảnh ghi "Trúng thầu: LD DVN", DB không có trường người trúng thầu |
| Nguồn vốn | NSNN, nguồn chi sự nghiệp giáo dục 2026 | Khớp | Khớp |
| Thời gian thực hiện | 2026–2027, thi công 120 ngày làm việc | Khớp | Khớp |
| Gói thầu chính: giá trị HĐ | 4.848.186.000 | 4.848.186.000 | Khớp |
| Gói thầu chính: số HĐ, ngày ký, hạn | 29/HĐKT-DVN, 21/09/2026, 120 ngày | Trống cả ba | **Thiếu** |
| TVGS: giá trị, số HĐ, ngày ký, hạn | 120.000.000; 24.8.26/HĐTV/SGDĐT-CRYSTAL; 24/08/2026; 150 ngày | Chỉ có giá trị 120.000.000 | **Thiếu** số HĐ, ngày, hạn |
| TVQLDA: giá trị, số HĐ, ngày ký, hạn | 109.000.000; 248/HĐKT-QLDA; 24/08/2026; 150 ngày | Chỉ có giá trị 109.000.000 | **Thiếu** số HĐ, ngày, hạn |
| TV lập HSMT, TV thẩm định KQLCNT, TV lập BCKTKT, TV thẩm tra BCKTKT | 23.000.000; 11.000.000; 214.148.189; 7.560.000 | Không có dòng nào | **Thiếu** cả bốn dòng |
| Chi phí phần mềm | 5.447.400.000 (giá trúng 4.848.186.000) | Không có trường này | **Thiếu** |
| Chi phí QLDA | 109.133.212 | Không có trường này | **Thiếu** |
| Chi phí tư vấn đầu tư | 380.919.349 | Không có trường này | **Thiếu**; xem lệch bên dưới |
| Chi phí khác / dự phòng | 62.046.379 / 0 | Không có trường này | **Thiếu** |
| Hạn giải ngân | 09/12/2026 | Không có trường này | **Thiếu** |

**Lệch nội bộ trong ảnh (cần bạn xác nhận):**
- Tổng các khoản chi (5.447.400.000 + 109.133.212 + 380.919.349 + 62.046.379 = 5.999.498.940) lệch 1 đồng so với tổng mức 5.999.498.939. Đây có thể là làm tròn.
- Chi phí tư vấn đầu tư 380.919.349 không bằng tổng các dòng tư vấn trong ảnh (214.148.189 + 23.000.000 + 11.000.000 + 7.560.000 + 120.000.000 = 375.708.189). Lệch 5.211.160 đồng. Có thể có khoản tư vấn chưa liệt kê.

**Dữ liệu DB không có trong ảnh (không nhập vào Tổng quan HCM):**
- Hợp đồng `Gói thầu chính` thuộc dự án SGD-LD-TB10-2026 (106.225.000.000, số HĐ HD2600226555_2609110905, ký 06/10/2026). Đây là dự án Lâm Đồng, không liên quan ảnh HCM.
- Quyết định `BUDGET_APPROVAL` 2065 (125.230.620.500) và `SUPERVISION_ASSIGNMENT` 3505 đều thuộc dự án Lâm Đồng.

**Kết luận Pha 0:** phần quyết định pháp lý và tổng mức khớp hoàn toàn với ảnh. Phần hợp đồng thiếu số HĐ, ngày ký, hạn và bốn dòng tư vấn. Chi phí theo khoản, mục III và phần nhập tay không có trong DB, nên sẽ là dữ liệu mới của Pha 1.

### Pha 1: Dữ liệu (chỉ khi chọn B hoặc C)
| ID | Việc | Trạng thái |
|---|---|---|
| 1.1 | Test đỏ cho API: bảng chi phí theo khoản và yêu cầu kỹ thuật trả đúng thứ tự, đúng định dạng | ✅ Đỏ vì thiếu module, sau đó xanh |
| 1.2 | Model, migration, schema Pydantic, service, router theo layering router → service → model | ✅ Migration `a7d3e9f2c1b8`, head mới; `alembic check` sạch |
| 1.3 | Mở rộng bảng hợp đồng: vai trò, đơn vị thực hiện, đầu mối, hiện trạng (nullable) | ✅ Thêm `contractor_name`, `role_label`, `contact_person`, `status_note` |
| 1.4 | Seed từ dữ liệu đã đối chiếu, idempotent, kiểm tra `alembic check` sạch | 🟡 Một phần. Xong: mục I (decision_authority, bốn khoản chi), TVGS và TVQLDA (số HĐ, ngày, hạn), bốn gói tư vấn từ ảnh (giá trị, vai trò, trạng thái). Chưa: mục III, đầu mối, hiện trạng của gói chính và TVGS/TVQLDA, tên đơn vị của bốn gói tư vấn |
| 1.5 | Ghi audit cho thao tác ghi (nếu có API ghi); kiểm tra downgrade | 🟡 Không có API ghi. Seed khoản chi và cập nhật hợp đồng không ghi audit (seed quyết định thì có). Downgrade chưa chạy thử |

### Pha 2: Hàm thuần và kiểu (web)
| ID | Việc | Trạng thái |
|---|---|---|
| 2.1 | Test đỏ trong `lib/overview-sections.test.ts`: định dạng ngày dd/mm/yyyy, tải khoản chi và yêu cầu kỹ thuật kèm token, lỗi HTTP | ✅ Đỏ vì thiếu module, sau đó xanh |
| 2.2 | Cập nhật `lib/overview.ts` theo kiểu mới | ✅ Thêm bốn trường hợp đồng. Fixture ở `overview.test.ts` và `contracts-view.test.tsx` đã bổ sung |

### Pha 3: Giao diện
| ID | Việc | Trạng thái |
|---|---|---|
| 3.1 | Viết lại `OverviewView` thành ba khối I, II, III. Điện thoại dùng thẻ, máy tính dùng bảng | ✅ Ba khối trong một DOM. Mục II và III là lưới CSS đổi theo breakpoint (1 cột, 2 cột, 4 cột), không render bảng riêng |
| 3.2 | Nội dung tiếng Việt có dấu, định dạng số và ngày theo vi-VN | ✅ Ngày dd/mm/yyyy, số có dấu chấm. Ô thiếu hiện "Chưa có nguồn" |
| 3.3 | Cập nhật `overview-view.test.tsx` và e2e | ✅ Unit test cập nhật. E2E chưa thêm |

### Pha 4: Kiểm chứng
| ID | Việc | Trạng thái |
|---|---|---|
| 4.1 | `make api-test`, `make api-lint`, `make web-test`, `make web-lint`, `make web-build` đều xanh | ✅ 602 test backend, coverage 84,75%; 217 test web; lint và build sạch |
| 4.2 | Playwright ở 375px và 1280px: không tràn ngang, các chuỗi chính hiển thị | ✅ `e2e/tracking-pages.spec.ts` 20/20 xanh trên Chromium và Pixel 5 (gồm kiểm tra tràn ngang cho overview); toàn bộ e2e 48/48 xanh. Thêm test ba mục và khoản chi |
| 4.3 | Đối chiếu lại từng ô với ảnh, ghi kết quả vào Nhật ký | 🟡 Đã đối chiếu mục I, II với ảnh độ phân giải cao. Còn: mục III (chờ file gốc), hiện trạng bị cắt ở 4 dòng |

## Validation

```bash
make api-test
make api-lint
make web-test
make web-lint
make web-build
```

## Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| CAO | Số liệu trong ảnh lệch với DB, hoặc với văn bản pháp lý gốc | Pha 0 đối chiếu, không tự chọn giá trị |
| CAO | Mục III không có nguồn dữ liệu, dễ bị nhập tay sai | Chốt câu hỏi 2 trước khi làm |
| TB | Đổi schema vi phạm plan tracking trước đó | Chốt câu hỏi 1 |
| TB | Bảng 9 cột bị cắt ở 375px | Thẻ trên điện thoại, bảng trên máy tính |
| TB | Chuyển tab gọi lại API `fetchProjectOverview` mỗi lần (đã hoãn cache) | Ghi lại, không làm trong plan này |

## Acceptance

- [ ] Ba khối I, II, III hiển thị đủ các ô có dữ liệu, ô thiếu hiển thị "Chưa có nguồn"
- [ ] Mọi số liệu đã đối chiếu, các chỗ lệch được ghi lại
- [ ] Validation xanh
- [ ] Không tràn ngang ở 375px và 1280px

## Nhật ký

| Ngày | Ghi chú |
|---|---|
| 2026-11-02 | Lập plan từ ảnh báo cáo mẫu |
| 2026-11-02 | Người dùng trả lời bốn câu: phương án C, thêm bảng cho mục III, Tổng quan hiển thị đầy đủ, có đối chiếu |
| 2026-11-02 | Người dùng trả lời ba câu: thêm 3 cột vào `projects` (migration `b8e2f1c4d7a3`), dòng Chủ đầu tư là một dòng riêng ở mục II, giữ tên dự án như DB. Đã làm: API và seed thêm đại diện pháp luật, hình thức QLDA, hạn giải ngân; web hiển thị ba ô này và dòng Chủ đầu tư (ô "Đầu mối" và "Hiện trạng" của CĐT để trống vì ảnh có nhưng chưa seed). Kết quả: 602 test backend xanh, 217 test web xanh, `tsc` sạch, lint sạch, `alembic check` sạch, DB dev đã migrate và seed |
| 2026-11-02 | Đối chiếu lại với ảnh độ phân giải cao (images/2.png). Sửa seed `hcm_contracts.json`: số HĐ, ngày ký, đơn vị, đầu mối, hiện trạng của Gói thầu chính, TVGS, TVQLDA và bốn gói tư vấn. Sửa trực tiếp 4 hiện trạng do mình đoán ở Pha 1 (HSMT đúng là "Đã bàn giao; Biên bản nghiệm thu còn thiếu"; ba gói còn lại để trống vì ảnh cắt). Còn lệch, chờ quyết định: (a) mục I thiếu đại diện pháp luật, hình thức QLDA, hạn giải ngân (DB không có trường); (b) dòng Chủ đầu tư trong mục II chưa biểu diễn; (c) tên dự án ảnh có tiền tố "Hoạt động ứng dụng CNTT" trong khi DB không có; (d) hiện trạng bị cắt ở 4 dòng, và thời hạn "120 ngày làm việc (kết thúc ~09/12/2026)" của gói chính chưa lưu |
| 2026-11-02 | Người dùng trả lời: giữ đủ 4 gói tư vấn (spec §7 chỉ có 3, cần xác nhận lại nếu spec đổi); mục III sẽ gửi đường dẫn file Excel gốc; làm Pha 2–3 ngay. Pha 2–3 xong: 215 test web xanh, `tsc` sạch, lint sạch, `make web-build` thành công. Chưa chạy Playwright ở 375px và 1280px (Pha 4.2). Test `overview-view.test.tsx` được viết trước nhưng không chạy riêng ở trạng thái đỏ |
| 2026-11-02 | Pha 1 (API và seed phần mục I, II): 599 test backend xanh, `make api-lint` sạch, `alembic check` sạch sau khi áp migration lên DB dev, seed chạy lại không tạo trùng. Lệch so với plan: (a) spec §7 chỉ có 3 hợp đồng HCM, bốn gói tư vấn lấy từ ảnh. Đã sửa `test_seed_contracts.py` để kiểm tra ba gói theo spec và thêm 4 gói từ ảnh; cần bạn xác nhận vì spec là nguồn sự thật; (b) ảnh độ phân giải thấp, bốn gói tư vấn chỉ có giá trị, vai trò, trạng thái, nên số HĐ và tên đơn vị để trống; (c) mục III chưa seed vì chưa có văn bản đọc rõ |
| 2026-11-02 | Người dùng xác nhận "proceed". Pha 0 xong: đối chiếu với DB dev, chi tiết ở mục Pha 0. Chưa sửa code. Chờ người dùng quyết định về ba điểm: cơ quan quyết định đầu tư trống trong DB, lệch 5.211.160 đồng trong ảnh, và có nhập số HĐ/ngày ký/hạn của TVGS và TVQLDA từ ảnh vào DB không |
| 2026-11-02 | Người dùng trả lời ba điểm: (a) nhập "Ủy ban nhân dân Thành phố Hồ Chí Minh" vào `decision_authority` của SGD-HCM-CSVC-2026; (b) tổng tư vấn hiển thị nguyên như ảnh 380.919.349 đ, ghi chú không khớp các dòng; (c) nhập số HĐ, ngày ký, hạn của TVGS và TVQLDA từ ảnh. Sẵn sàng bắt đầu Pha 1 |
