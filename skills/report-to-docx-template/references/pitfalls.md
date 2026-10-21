# Bài học & checklist

## Lỗi đã gặp
| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Biến không map được dù tên cột đúng | Token gõ trong Word bị chèn khoảng trắng/run: `{#sign ing _date#}` | Dựng bằng `docx_kit.js`; với file Word có sẵn: xoá token, gõ lại liền 1 lần (tắt autocorrect), chạy `check_template.py` |
| Cột list lệch hàng nửa sau trang | 1 ô chữ bị wrap thành 2 dòng | `SUBSTR` theo độ dài tối đa của cột; giảm cỡ chữ list (7.5pt) |
| Cột list lệch hàng từ đầu | Số dòng giữa các cột khác nhau (NULL bị bỏ, ORDER BY khác) | Cùng ORDER BY; NULL → dòng trống; `check_template.py` báo lệch theo tiền tố |
| Số in `1234567.0` | Dataset trả NUMBER, mapping để `raw` | Mapping `vi`/`custom`, hoặc định dạng ở SQL (`F_RPT_SO`) |
| Ngày in `2024-12-24` | Dataset trả DATE, mapping `raw` → `isoformat()` | Mapping `date` `DD/MM/YYYY`, hoặc `TO_CHAR` trong SQL |
| So khớp chuỗi tiếng Việt từ PDF thất bại | PDF dùng Unicode tổ hợp (NFD) | `unicodedata.normalize("NFC", ...)` (đã có trong `pdf_probe.py`, `samples.py`) |
| Tên người trong PDF nhật ký quỹ ra ký tự rác | Font PDF gốc lỗi mã hoá | Nhập tay dữ liệu mẫu (`NKQ_USD` trong samples.py) |
| Tổng CĐTK cấp III không thẳng cột khi trích | Dòng tổng canh trái | Lấy theo thứ tự xuất hiện thay vì theo `edges` |
| Tên TK xuống dòng trong PDF thành 2 dòng | Wrap của báo cáo gốc | Nối vào dòng trước khi dòng không có mã TK/số |
| Template > 200 biến | Bảng fixed quá lớn | Tách template, hoặc chuyển phần dài sang pattern list |
| Font PDF trên server khác local | Converter thiếu Times New Roman | Upload ZIP font, set `reportPdf.fontBundleKey` |
| Upload bị từ chối "embedded objects" | Dán bảng Excel/OLE vào Word | Dựng bảng Word thuần; logo là PNG |
| "Invalid repeating row tXrY. Use a plain body row..." | Dòng lặp có ô gộp dọc / lặp tiêu đề / ảnh / bookmark | Dùng `repeatRow()`; gộp dọc chỉ đặt ở dòng tiêu đề |
| "Variable X has different values in one report" | Biến chung để `constant` nhưng giá trị khác nhau trong group | Thêm cột vào Group by, hoặc chọn `first`/`sum`... |
| "Use unformatted numeric values for X" | Cấu hình `vi`/`custom`/`sum` trên cột đã là chuỗi `1.234` | View trả số thô, hoặc để `raw` |
| Tổng phần A ra bằng tổng A+B | Aggregate tính trên cả group, không theo filter dòng lặp | Cột tổng theo phần trong view + `first` |
| Dòng chi tiết sai thứ tự / xen nhóm | Report chỉ sort 1 cột | `sort_key` = phần + STT có `LPAD` |
| Preview multi_row thiếu dòng | Preview chỉ lấy 5 dòng dữ liệu đầu | Bình thường; kiểm tra đủ bằng export hoặc `check_template.py` |
| "A report must contain between 1 and 2,000 data rows" | Group quá lớn | Thêm cột group (vd theo trang/phần) hoặc tăng `REPORT_BUILDER_MAX_ROWS_PER_REPORT` |
| "Results exceed 5,000 rows" khi tải dữ liệu | Giới hạn mỗi lần tải | Lọc theo đơn vị/kỳ trước; tăng `REPORT_BUILDER_MAX_EXPORT_ROWS` |
| Hai dòng lặp liền nhau không xen kẽ | Engine chèn hết bản sao dòng 1 rồi đến dòng 2 | Dòng nhóm là dữ liệu trong cùng 1 dòng lặp |
| Dashboard: "needs exactly one {#dashboard#} ... own paragraph" | Slot nằm trong bảng/header hoặc lẫn chữ khác | Đoạn riêng trong thân văn bản; 1 lần duy nhất |
| Dashboard: "must use a single-column Word layout" | Section chứa slot có nhiều cột | Section 1 cột |
| Người dùng không thấy template dashboard | Chưa Publish / người publish không còn là Admin | Admin Publish lại |
| docx dựng lại khác XML bản cũ (`cantSplit off/false`, `tcW`) | Khác phiên bản npm `docx` | Không ảnh hưởng hiển thị; pin `docx@9` nếu cần so sánh byte |

## Checklist bàn giao 1 template
- [ ] `check_template.py <docx> [--mode ...] --data <json> --pdf` exit 0, số biến ≤ 200
- [ ] multi_row: ghi rõ Group by, Repeat rows (tXrY + filter), Sort, định dạng/aggregate từng biến (mapping.json)
- [ ] dashboard: slot hợp lệ, liệt kê biến text cần nhập/gán filter, đã Publish
- [ ] PDF điền thử đặt cạnh PDF gốc: tiêu đề, header phải, độ rộng cột, căn lề số, xuống dòng, ngắt trang, khối ký
- [ ] Số âm đúng quy ước (B02 `(x)`, còn lại `-x`), số lẻ đúng loại tiền
- [ ] Tổng cộng khớp PDF gốc (`samples.py` có `assert` số dòng)
- [ ] `Cau_truc_du_lieu.xlsx` + `Cau_truc_du_lieu_Oracle.sql` cập nhật, grain ghi rõ
- [ ] Giá trị dài nhất < 50.000 ký tự với kỳ/đơn vị lớn nhất dự kiến
- [ ] Upload thử lên `/report-templates/`, auto-mapping không còn biến "Column unavailable"
- [ ] Preview PDF trên server (font) OK
