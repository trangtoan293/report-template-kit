---
description: Chuyển báo cáo mẫu (PDF/Word) thành template DOCX cho Superset Report Builder / Dashboard Export
argument-hint: <file báo cáo mẫu...> [per_row|multi_row|dashboard]
---

Dùng skill `report-to-docx-template` để chuyển báo cáo mẫu sau thành template DOCX: $ARGUMENTS

Thực hiện đủ quy trình B0–B7 của skill:
1. Chuẩn bị `Templates/_src/` (copy scripts, `sync_engine.py` từ các file `values-*.yaml` trong dự án).
2. Khảo sát từng PDF bằng `pdf_probe.py`, rồi **đề xuất** loại template (per_row / multi_row / dashboard), grain và
   cột group (multi_row) kèm căn cứ, và **hỏi người dùng xác nhận bằng AskUserQuestion** (bước B2 của skill).
   Loại ghi trong tham số chỉ là gợi ý. Chỉ dựng template sau khi người dùng đã chọn.
3. Đặt tên biến theo `references/data-contract.md`, dựng template bằng `docx_kit.js`.
4. Sinh dữ liệu mẫu từ chính PDF, đặc tả dataset + SQL view.
5. Chạy `check_template.py` (đúng chế độ) với `--pdf`, so sánh PDF điền thử với PDF gốc, sửa đến khi khớp.
6. Báo cáo kết quả: file template, số biến, cấu hình report (group by / repeat rows / sort / định dạng), file SQL/Excel,
   các điểm còn khác so với bản gốc.
