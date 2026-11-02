# Mẫu báo cáo E11 (bản nháp tự tạo, chờ duyệt)

> **Trạng thái:** bản nháp để duyệt trước khi làm E11 pha 2. Đây không phải mẫu chính thức của
> An Lập Thịnh hay Crystal, và **chưa đối chiếu thể thức Nghị định 30/2020** (font, cỡ chữ, lề,
> quốc hiệu, số trang). Cần file mẫu thật (Q1, Q2) trước khi xuất `.docx`.
>
> **Chưa xuất `.docx`:** môi trường chưa cài `python-docx`, và `pyproject.toml` chưa khai báo nó.
> Thêm dependency là quyết định riêng.

Kỳ báo cáo: tuần từ Thứ Hai đến Chủ nhật (G1). Ví dụ: tuần 03 là 26/10–01/11/2026.
Mọi số liệu lấy từ dữ liệu tại thời điểm xuất, rồi lưu snapshot (G2).

## Mẫu 1: Báo cáo QLDA tuần (`PM_WEEKLY`)

| # | Mục | Placeholder | Nguồn dữ liệu (bảng / model) |
|---|---|---|---|
| 1 | Thông tin dự án | `{project.code}`, `{project.name}`, `{period.start}`, `{period.end}` | `projects`, kỳ tuần |
| 2 | Tiến độ mốc | `{milestones.done}`, `{milestones.open}`, `{milestones.late}` | `milestones_wbs` (`Milestone`) |
| 3 | Mốc đến hạn trong tuần | danh sách `{milestone.code} {milestone.name} {milestone.due}` | `milestones_wbs` |
| 4 | Rủi ro và vướng mắc | `{risks.open}`, danh sách `{risk.code} {risk.title}` | `project_risks_and_issues` (`RiskIssue`) |
| 5 | Hợp đồng | `{contract.number}`, `{contract.value}`, `{contract.expiration}` | `contracts` (`Contract`) |
| 6 | Hồ sơ pháp lý | `{legal.pending}` | `legal_documents` (chờ xác định trạng thái, Q4) |
| 7 | Giao hàng, serial | `{serials.delivered}`, `{serials.missing}` | `equipment_serials`, `delivery_handovers` |
| 8 | Kiến nghị theo đối tượng | nhóm theo `{target}`: Nhà thầu, CĐT, Đơn vị thụ hưởng, TVGS, TVQLDA | `project_risks_and_issues` (cần cột phân loại, Pha 3) |
| 9 | Kế hoạch tuần tới | `{plan.next_week}` | nhập tay |

## Mẫu 2: Báo cáo giám sát tuần (`SUPERVISION_WEEKLY`)

| # | Mục | Placeholder | Nguồn dữ liệu |
|---|---|---|---|
| 1 | Thông tin gói giám sát | `{project.code}`, `{contract.number}` (gói TVGS) | `projects`, `contracts` |
| 2 | Điểm dừng kiểm tra (hold points) | `{hold.open}`, `{hold.confirmed}` | `hold_points`, `hold_point_confirmations` |
| 3 | Đơn vị thụ hưởng đã khảo sát | `{beneficiary.surveyed}` / `{beneficiary.total}` | `beneficiary_units` |
| 4 | Vướng mắc tại hiện trường | danh sách rủi ro/vấn đề mở | `project_risks_and_issues` |
| 5 | Kết luận và kiến nghị | nhập tay | — |

## Mẫu 3: Meeting note giao ban (`MEETING_NOTE`)

| # | Mục | Placeholder | Nguồn dữ liệu |
|---|---|---|---|
| 1 | Thời gian và thành phần | `{meeting.date}`, `{meeting.attendees}` | nhập tay |
| 2 | Nội dung đã thảo luận | `{meeting.points}` | nhập tay hoặc AI bóc tách (E11 pha 4, bản nháp) |
| 3 | Quyết định | `{meeting.decisions}` | nhập tay, người dùng duyệt |
| 4 | Việc cần làm | bảng `{task.owner}`, `{task.due}`, `{task.content}` | nhập tay hoặc AI bóc tách (bản nháp) |

## Quy tắc trộn dữ liệu (đề xuất)

- Placeholder không có dữ liệu thì ghi **"chưa có dữ liệu"**, không ghi 0 (G4 của E12).
- Mọi số liệu lấy tại thời điểm xuất và lưu vào `weekly_reports.data_snapshot`. Xuất lại cùng kỳ tạo bản mới có số thứ tự tăng dần, không ghi đè.
- Biên bản do AI sinh luôn là `DRAFT`, chưa có chữ ký (G4 của E11).

## Câu hỏi cần trả lời để chốt mẫu

1. Có file mẫu thật của An Lập Thịnh và Crystal để đối chiếu thể thức không (Q1, Q2)?
2. Mục 6 (hồ sơ pháp lý) lấy trạng thái nào từ `legal_documents`?
3. Mục 7 (serial thiếu) dùng định nghĩa "thiếu" nào?
