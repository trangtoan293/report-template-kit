# Hợp đồng engine (đối chiếu code YAML v1.5.x, 2026-10)

## 0. Ba file Helm values
| File | Nội dung | Liên quan template |
|---|---|---|
| `values-report-builder.yaml` | Report Builder v2: `/report-templates/`, `/reports/`, `/report-builder/?template=<id>`; sidecar Gotenberg LibreOffice; worker export tuỳ chọn | **Có** – loại A, B; Publish template cho dashboard |
| `values-dashboard-export.yaml` | Dashboard Export: Download → Export dashboard / Export chart; worker riêng, LibreOffice + Chromium | **Có** – loại C (`{#dashboard#}`) |
| `values-reporting-combined.yaml` | Overlay ghép 2 tính năng: khoá ghi S3 cho OCI (`reportingStorage.writeMode: auto` → PostgreSQL advisory lock), dùng chung font bundle, worker chuyên dụng | Không đổi cú pháp template; chỉ triển khai |

Thứ tự helm: `... -f values-report-builder.yaml -f values-dashboard-export.yaml -f values-reporting-combined.yaml` (combined luôn cuối).

Module trong `extraConfigs` (mount `/app/pythonpath/customsso/`):
| Module | Vai trò |
|---|---|
| `rt_office.py` | Đọc/kiểm tra template, tìm biến, `merge` phẳng, HTML preview |
| `rt_format.py` | Định dạng số/ngày/text theo mapping; aggregate + công thức |
| `rt_multi.py` | Chế độ `multi_row`: group, dòng lặp, giá trị chung |
| `report_workflow.py` | API upload/publish/preview/rows/export-plan/export |
| `rt_pdf.py`, `rt_pdf_fonts.py` | Convert PDF/A-2b qua Gotenberg; font ZIP từ S3 |
| `rt_jobs.py`, `rt_job_worker.py` | Export nền + lịch sử (khi `reportExportWorker.enabled: true`) |
| `dr_docx.py`, `dr_templates.py`, `dashboard_export.py`, `dr_worker.py` | Dashboard Export (file thứ 2) |

## 1. Cú pháp biến (`rt_office.py`)
```python
TOKEN = re.compile(r"\{#\s*([^#{}\[\]\r\n]{1,128}?)\s*#\}|\[#\s*([^#{}\[\]\r\n]{1,128}?)\s*#\]")
```
- `{#ten#}` / `[#ten#]`, 1–128 ký tự; khoảng trắng 2 đầu bị bỏ, **giữa** thì giữ (`{#sign ing#}` là tên khác).
- Token có thể trải nhiều run trong **cùng 1 đoạn**, không vắt qua đoạn/ô.
- Part được quét: `word/document.xml`, `header*.xml`, `footer*.xml`, `footnotes.xml`, `endnotes.xml`.
- Upload bị từ chối khi: không phải docx/xlsx; > 10 MB; > 1500 part / > 60 MB giải nén; mã hoá; có `vbaProject`,
  `/embeddings/`, `externalLinks/`, `activeX/`; relationship External (trừ hyperlink); XML có DOCTYPE/ENTITY;
  0 biến; > 200 biến.

## 2. Mapping & định dạng (`report_workflow.auto_mapping`, `rt_format.py`)
- Auto-map: trùng tên cột; nếu không thì trùng `casefold()` duy nhất; còn lại "Leave blank".
- Mỗi binding: `number_format` ∈
  | Giá trị | Kết quả |
  |---|---|
  | `raw` (mặc định) | `display()`: `None→""`, date → ISO `2024-12-24`, số → `str()` |
  | `vi` + `decimals` 0–6 | `1.234.567,50`; âm `-1.234` |
  | `en` | `1,234,567.50` |
  | `date` + `date_format` | token `YYYY YY MM DD HH mm ss`, chữ cố định trong `[...]`; nhận ISO hoặc `dd/mm/yyyy` |
  | `custom` number | mẫu `#.##0,00`, `#,##0.00`, `0.00%`, âm riêng: `#.##0;(#.##0)` |
  | `custom` date / text | mẫu ngày / `Số dư: {value}` |
- Định dạng số yêu cầu giá trị **số thô** (chuỗi đã format → lỗi "Use unformatted numeric values").

## 3. Chế độ per_row (loại A)
- 1 dòng dataset → `office.merge(row_values(...))` → 1 file. Nhiều dòng chọn → ZIP nhiều PDF.
- `\n` trong giá trị → `w:br` (xuống dòng trong ô) — nền tảng của pattern list cũ.

## 4. Chế độ multi_row (loại B, `rt_multi.py`)
| Thành phần | Quy tắc |
|---|---|
| `report_mode` | `per_row` \| `multi_row` (multi_row chỉ cho DOCX) |
| `group_by` | ≤ 8 cột; group theo giá trị JSON của các cột, giữ thứ tự xuất hiện; group rỗng = toàn bộ dòng chọn là 1 báo cáo |
| `repeat_rows` | 1–12 dòng; ID `t<bảng>r<dòng>` đánh số theo thứ tự `w:tbl`/`w:tr` trong `word/document.xml` (kể cả bảng khối ký; bảng ở header không tính) |
| filter dòng lặp | `filter_column` + `filter_value` (so sánh chuỗi `display(value) == value`) → cùng dataset tách phần A/B |
| Dòng lặp hợp lệ | có ≥ 1 biến; KHÔNG chứa `tbl` lồng, `vMerge`, `tblHeader`, bookmark, comment, `drawing/pict`, `sectPr`, foot/endnote ref; không nằm trong bảng lồng |
| Biến trong dòng lặp | điền từ từng dòng dữ liệu (đã định dạng) |
| Biến chung (ngoài dòng lặp, cả header/footer) | aggregate: `constant` (mặc định – lỗi nếu khác nhau trong group), `first`, `sum`, `avg`, `min`, `max`, `count`, `custom` (công thức `SUM("col")`, `+ - * /`, ≤ 256 ký tự) |
| Giới hạn | 1–`REPORT_BUILDER_MAX_ROWS_PER_REPORT` (2000) dòng/báo cáo; ≤ 5.000 dòng bảng sinh; ≤ 50.000 ký tự/giá trị; docx ≤ 60 MB |
| Sort | đúng **1 cột** `order` (+ `descending`) ⇒ view cần cột `sort_key` xếp đúng thứ tự dòng trong group |
| Tải dữ liệu | `REPORT_BUILDER_MAX_EXPORT_ROWS` (5000) dòng/lần, snapshot ≤ 20 MB, hết hạn 30 phút; ≤ 20 filter |
| Preview | chỉ 5 dòng đầu ⇒ báo cáo multi_row xem trước bị thiếu dòng (bình thường) |

Aggregate tính trên **cả group**, không theo filter của dòng lặp ⇒ tổng riêng từng phần (A/B) phải là cột dataset
(`SUM() OVER (PARTITION BY key, phan)` rồi pivot) + aggregate `first`.

## 5. Dashboard Export (loại C, `dr_docx.py`)
- Đúng 1 `{#dashboard#}`, đứng trong đoạn riêng ở thân văn bản (không trong bảng, header, footer); lỗi:
  "The DOCX template needs exactly one {#dashboard#} variable in its own paragraph."
- Section chứa slot phải 1 cột; vùng in ≥ 1800 twip. Font bảng sinh = font của đoạn slot/`styles.xml`.
- `{#datetime#}` dành riêng: "ngày dd tháng mm năm yyyy" theo `REPORT_TIMEZONE` (Asia/Ho_Chi_Minh).
- Biến khác: người export nhập text hoặc gán **giá trị filter đang áp dụng** của dashboard (≤ 2.000 ký tự).
- Bảng chart được stream vào slot: tiêu đề, "Bộ lọc áp dụng", chia block `docxTableRowsPerBlock` (200) dòng, lặp header,
  `columnsPerGroup` (8) cột/nhóm khi bảng rộng; `maxRowsPerQuery` 500.000, `maxDocxXmlMb` 100, `maxPdfMb` 200.
- Chỉ Admin upload; Admin **Publish** template DOCX có `{#dashboard#}` thì người dùng mới chọn được.

## 6. PDF & font
- LibreOffice trong Gotenberg → PDF/A-2b; `reportPdf.timeoutSeconds` (≤ 1200); PDF ≤ 40 MB (report builder).
- Không ép font: font khai báo trong template phải có trên converter ⇒ ZIP font (Times New Roman...) ở S3,
  `reportPdf.fontBundleKey` (+ `fontBundleSha256`) — combined overlay dùng chung cho cả 2 converter.
- Kiểm tra local (`check_template.py --pdf`, `soffice`) ≈ server; khác biệt chủ yếu do font.
