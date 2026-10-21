# report-template-kit

Plugin Claude Code: chuyển **báo cáo mẫu** (PDF/Word ngân hàng) thành **template DOCX** cho Superset
(`values-report-builder.yaml` – Report Builder, `values-dashboard-export.yaml` – Dashboard Export).

## Cài đặt
```bash
# trong Claude Code
/plugin marketplace add trangtoan293/report-template-kit
/plugin install report-template-kit@report-template-kit
/reload-plugins
```
Cập nhật bản mới: `/plugin marketplace update report-template-kit` rồi `/reload-plugins`.
Yêu cầu máy: Node ≥ 18 + `npm i -g docx@9`; Python 3 + `pip install pymupdf openpyxl`; LibreOffice (`soffice`).
Plugin kèm 3 file Helm values mẫu (v1.5.4) ở `skills/report-to-docx-template/examples/superset-values/`;
nếu dự án có bản đang deploy thì dùng bản của dự án. PDF mẫu không kèm theo: đặt trong thư mục dự án.
Dữ liệu nhập tay trong `examples/bm01-bm07/samples.py` đã được ẩn danh.

## Dùng
- Lệnh: `/report-template KQKD_TNH_24-12-2024.pdf` (tuỳ chọn thêm `per_row` | `multi_row` | `dashboard`).
- Hoặc nói tự nhiên: "chuyển báo cáo mẫu này thành template docx cho report builder" → skill `report-to-docx-template` tự kích hoạt.

## Theo dõi tiến độ
- **Status line**: `📄 report-template · 5/8 B4 Dựng template` (B6 kèm `✓ đạt` / `✗ còn lỗi`).
- **Panel "Report template"** (tự mở lần đầu, mở lại bằng `/report-template-progress`):
  - thanh tiến độ `█████░░░ 5/8` + thời gian chạy;
  - 8 bước B0–B7: `✓` xong · `▶` đang chạy · `✗` lỗi · `○` chưa tới; bước hiện tại có mô tả, mỗi bước ghi kết quả gần nhất;
  - **Nhật ký**: 8 lệnh gần nhất (`+1m05s  B6  check_template.py BM04M.docx  ✗ Invalid repeating row t1r3`);
  - ô **Tiếp theo / Cần sửa** nói việc kế tiếp.
Bước được nhận diện qua lệnh Claude chạy (`sync_engine.py`, `pdf_probe.py`, câu hỏi xác nhận, `node build*.js`,
`outputs.py`/`multi_data.py`, `check_template.py`).

## Ba loại template được hỗ trợ (engine v1.5.x)
| Loại | Dùng cho | Cách engine điền |
|---|---|---|
| **per_row** | Chỉ tiêu cố định (B02, B03, Bảng 13), hợp đồng | 1 dòng dataset = 1 báo cáo |
| **multi_row** | Danh sách (CĐTK cấp III, sổ cái, nhật ký quỹ...) | Group theo ≤ 8 cột khoá; lặp 1–12 dòng bảng (lọc được theo cột); biến chung dùng aggregate |
| **dashboard** | Khung Word bọc dashboard/chart | `{#dashboard#}` → bảng chart; `{#datetime#}`; biến text/filter |

## Quy trình (tóm tắt — chi tiết trong `skills/report-to-docx-template/SKILL.md`)
| Bước | Việc | Công cụ |
|---|---|---|
| B0 | Workspace `Templates/_src`, trích engine từ YAML | `sync_engine.py` |
| B1 | Khảo sát PDF: bố cục, cột, toạ độ | `pdf_probe.py` |
| B2 | Claude **đề xuất** loại (per_row / multi_row / dashboard), grain, cột group → **người dùng xác nhận** | `AskUserQuestion`, `references/layout-patterns.md` |
| B3 | Đặt tên biến = tên cột dataset | `references/data-contract.md` |
| B4 | Dựng template bằng code | `docx_kit.js` (+ `examples/.../build*.js`) |
| B5 | Đặc tả dataset, SQL Oracle, dữ liệu mẫu từ PDF | `examples/.../make_data.py, samples.py, outputs.py, multi_data.py` |
| B6 | Điền thử bằng engine thật + PDF, so với bản gốc | `check_template.py` |
| B7 | Upload, mapping, group/repeat, export trên Superset | `references/engine-contract.md`, `pitfalls.md` |

## Cấu trúc
```
report-template-kit/
├── .claude-plugin/{plugin.json, marketplace.json}
├── commands/report-template.md
├── hooks/{hooks.json, register.tsx, register.test.ts}   # status line + panel tiến độ
├── types/index.d.ts                   # kiểu state của panel
└── skills/report-to-docx-template/
    ├── SKILL.md                       # quy trình B0–B7
    ├── references/
    │   ├── engine-contract.md         # ràng buộc engine, trích từ 3 file values YAML
    │   ├── layout-patterns.md         # đọc bố cục, chọn pattern, kích thước
    │   ├── data-contract.md           # tên biến, view per_row / multi_row, định dạng
    │   ├── pitfalls.md                # lỗi đã gặp + checklist bàn giao
    │   └── catalog.md                 # PDF mẫu → template
    ├── scripts/
    │   ├── sync_engine.py  check_template.py  pdf_probe.py  docx_kit.js
    ├── examples/superset-values/     # values-report-builder / dashboard-export / reporting-combined (mẫu)
    └── examples/bm01-bm07/      # nguồn BM01–BM07 + BM04M (multi_row) + DB01 (dashboard)
```

## Chạy lại ví dụ
```bash
mkdir -p /tmp/demo/Templates/_src && cp <PDF mẫu> /tmp/demo/
cp skills/report-to-docx-template/{scripts,examples/bm01-bm07}/* /tmp/demo/Templates/_src/
cd /tmp/demo/Templates/_src
python3 sync_engine.py . <values-report-builder.yaml> <values-dashboard-export.yaml>
NODE_PATH=$(npm root -g) node build.js && python3 outputs.py                       # BM01–BM07 + SQL + Excel
NODE_PATH=$(npm root -g) node build_multi.js && python3 multi_data.py               # BM04M
python3 check_template.py ../BM04M_Bang_can_doi_tai_khoan_cap_III_multi.docx --mode multi_row \
  --data ../_samples/BM04M_rows.json --mapping ../_samples/BM04M_mapping.json \
  --group-by ma_don_vi,tu_ngay,den_ngay,loai_nguyen_te --repeat t1r3:phan=A --repeat t2r3:phan=B --pdf
```
Đã kiểm chứng (2026-10-21) với YAML v1.5.4: 7 template per_row, BM04M (806 dòng → 1 báo cáo, 24 trang) và DB01 đều qua engine.
