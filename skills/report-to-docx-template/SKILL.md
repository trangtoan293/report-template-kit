---
name: report-to-docx-template
description: Chuyển báo cáo mẫu (PDF/Word của ngân hàng - CĐKT B02, KQKD B03, Bảng 13, CĐTK cấp III, sổ cái, nhật ký quỹ, TK cấp 4...) thành template .docx có biến {#ten_cot#} cho Superset Report Builder (values-report-builder.yaml - chế độ per_row hoặc multi_row group + lặp dòng bảng) hoặc Dashboard Export (values-dashboard-export.yaml - {#dashboard#}), kèm đặc tả dataset, SQL Oracle và file điền thử bằng đúng engine đang deploy. Dùng khi người dùng muốn "làm template", "chuyển báo cáo mẫu sang docx", "dựng biểu mẫu cho report builder", "map báo cáo vào Superset".
---

# Báo cáo mẫu → Template DOCX cho Superset (Report Builder / Dashboard Export)

Skill đóng gói quy trình đã dùng để dựng BM01–BM07 (dự án Core Banking) từ PDF mẫu, cập nhật theo engine v1.5.x.
Base directory của skill (hiện khi skill được nạp) gọi là `<SKILL_DIR>`.

## 0. Ba loại template — chọn trước khi làm

| Loại | Engine | Khi nào dùng | Dataset |
|---|---|---|---|
| **A. per_row** – 1 dòng = 1 báo cáo | `rt_office.py` | Báo cáo chỉ tiêu cố định (B02, B03, Bảng 13), giấy tờ/hợp đồng | "ngang": mỗi ô = 1 cột (pivot) |
| **B. multi_row** – group theo key, lặp dòng bảng | `rt_multi.py` + `rt_format.py` | Báo cáo danh sách: CĐTK cấp III, sổ cái, nhật ký quỹ, TK cấp 4 | "dài": 1 dòng = 1 dòng chi tiết, kèm cột key + header |
| **C. dashboard** – khung Word bọc dashboard | `dr_docx.py` (Dashboard Export) | Xuất dashboard/chart Superset ra PDF theo mẫu đơn vị | không cần; bảng lấy từ chart |

Ràng buộc chính (chi tiết + trích code: `references/engine-contract.md`):
- Biến `{#ten#}` (hoặc `[#ten#]`), auto-map với cột **cùng tên** (không phân biệt hoa thường). ≤ **200 biến**, giá trị ≤ 50.000 ký tự.
- **multi_row**: group theo ≤ 8 cột; lặp **1–12 dòng bảng** (ID `tXrY` = bảng X, dòng Y trong thân văn bản), mỗi dòng
  lặp có thể lọc `cột = giá trị` (vd phần A/B); biến ngoài dòng lặp tính bằng aggregate
  (`constant` – phải giống nhau trong group, `first`, `sum`, `avg`, `min`, `max`, `count`, công thức `SUM("a")/COUNT("a")`).
  ≤ 2.000 dòng dữ liệu/báo cáo, ≤ 5.000 dòng bảng sinh ra, ≤ 5.000 dòng/lần tải dữ liệu export. Sort chỉ **1 cột**.
  Dòng lặp không được chứa ô gộp dọc (rowSpan/vMerge), thuộc tính lặp tiêu đề, bookmark, ảnh, bảng lồng.
- **Định dạng** số/ngày cấu hình ở mapping (`raw`, `vi` + số lẻ, `en`, `date` `DD/MM/YYYY`, `custom` `#.##0;(#.##0)`);
  muốn aggregate thì dataset phải trả **số thô**. Định dạng sẵn trong SQL vẫn được (để `raw`).
- **dashboard**: đúng 1 `{#dashboard#}` trong đoạn riêng ở thân (không trong bảng/header/footer), section 1 cột;
  `{#datetime#}` hệ thống điền "ngày dd tháng mm năm yyyy"; biến khác nhập text/gán filter (≤ 2.000 ký tự); Admin phải Publish.
- Không macro / OLE / external link, file ≤ 10 MB. PDF qua LibreOffice (Gotenberg) PDF/A-2b → font phải có trong
  `reportPdf.fontBundleKey`.

## Quy trình 7 bước

### B0. Chuẩn bị workspace
```bash
mkdir -p Templates/_src && cd Templates/_src
cp <SKILL_DIR>/scripts/{docx_kit.js,check_template.py,pdf_probe.py,sync_engine.py} .
python3 sync_engine.py . <path>/values-report-builder.yaml [<path>/values-dashboard-export.yaml]   # -> customsso/
```
Ưu tiên file `values-*.yaml` của dự án (đúng bản đang deploy). Dự án chưa có thì dùng bản mẫu đi kèm plugin
(v1.5.4, 2026-10): `<SKILL_DIR>/examples/superset-values/values-report-builder.yaml`,
`values-dashboard-export.yaml`, `values-reporting-combined.yaml`.
Yêu cầu: Node + `docx` (`npm i -g docx@9`), Python 3 + `pymupdf openpyxl`, LibreOffice (`soffice`).
PDF mẫu đặt ở thư mục gốc dự án (cha của `Templates/`). Luôn sync lại khi YAML đổi phiên bản.

### B1. Khảo sát báo cáo mẫu
```bash
python3 pdf_probe.py "../../KQKD_TNH_24-12-2024.pdf" --pages 1 --lines 80
```
Ghi: khổ/hướng, header trái-giữa-phải, cột (2 tầng Nợ/Có), dòng cố định hay thay đổi, dòng tổng, khối ký, "Trang x/y",
đơn vị tính, quy ước âm `(x)`/`-x`, số lẻ. `Mép phải các cột số` = `edges` để trích số mẫu (B5).
Checklist đầy đủ: `references/layout-patterns.md` §1.

### B2. Đề xuất loại + pattern → NGƯỜI DÙNG XÁC NHẬN (bắt buộc)
Người dùng là người hiểu báo cáo; Claude **chỉ đề xuất**. Không dựng template (B3 trở đi) khi chưa có xác nhận.
1. Với từng báo cáo, trình bày đề xuất kèm căn cứ quan sát từ PDF: loại (`per_row` / `multi_row` / `dashboard`),
   "1 báo cáo = ?" (grain), và với `multi_row`: cột group đề xuất, các bảng/dòng sẽ lặp, filter phần (A/B...) nếu có.
2. Hỏi bằng `AskUserQuestion` (1 câu / báo cáo, tối đa 4 câu / lần): phương án đề xuất đặt đầu, ghi "(Đề xuất)";
   các phương án còn lại kèm hệ quả ngắn (vd per_row ⇒ danh sách phải gộp nhiều dòng trong SQL).
   Người dùng có thể chọn "Other" để nêu grain/cột group khác.
3. Tham số loại trong lệnh (`/report-template x.pdf multi_row`) chỉ là gợi ý ban đầu — vẫn xác nhận lại grain/cột group.
4. Ghi quyết định đã xác nhận vào báo cáo kết quả và `catalog.md` của dự án.

Gợi ý để đề xuất:
- Danh mục chỉ tiêu cố định → **A. per_row / fixed**: biến `<prefix>_rNN_<đo>`, danh mục dòng ở `rows.js` `[STT, Tên, H|B|N|S]`.
- Số dòng phụ thuộc dữ liệu → **B. multi_row / repeat** (khuyến nghị): 1 dòng bảng chứa token đơn `{#ten_tk#}`...,
  tổng dùng aggregate `sum` hoặc cột tổng có sẵn + `first`. Nhiều phần (A/B) = nhiều bảng, mỗi bảng 1 dòng lặp có filter.
- Cách cũ cho list trên per_row (biến nhiều dòng nối `\n`, `listRow()`) chỉ dùng khi buộc phải 1 dòng/báo cáo.
- Xuất từ dashboard → **C**.
Bảng quyết định + kích thước: `references/layout-patterns.md`.

### B3. Đặt tên biến (hợp đồng dữ liệu)
Chuẩn chung: `ten_ngan_hang, ten_don_vi, don_vi_tinh, thang_bc, tu_ngay, den_ngay, bieu_mau, can_cu_ban_hanh`,
khối ký `ngay_ky, thang_ky, nam_ky, nguoi_lap, nguoi_kiem_soat, lanh_dao`, 6 cột kế toán `dk_no dk_co ps_no ps_co ck_no ck_co`.
Chữ cố định của biểu mẫu để cứng; chỉ biến hoá phần đổi theo đơn vị/kỳ. Chi tiết: `references/data-contract.md`.

### B4. Dựng template bằng code (không gõ tay token trong Word)
`docx_kit.js`: `pageHeader, table, hdr, H, noCo, fixedRow, repeatRow, listRow, totalRow, signatures, SIGN_STD, save`.
```js
const K = require('./docx_kit');
await K.save('../BM04M.docx', 'landscape', head, [
  K.table(W, [K.hdr([...]), K.noCo(W, 3),
    K.repeatRow([['ten_tk', K.L], ['tk_nhnn', K.C], ...K.AMT6.map((f) => [f, K.R])], W),   // t1r3
    K.totalRow('Tổng cộng:', W[0] + W[1] + W[2], 3, W, 3, 'tong_a')]),
  ...K.SIGN_STD(K.LANDSCAPE_W)]);
```
Ví dụ đầy đủ: `examples/bm01-bm07/build.js` (A), `build_multi.js` (B), `build_dashboard.js` (C).
Chạy `NODE_PATH=$(npm root -g) node build.js`. Lý do dựng bằng code: token nằm trọn 1 run, dựng lại được,
header bảng lặp mỗi trang, khối ký không tách trang. File Word có sẵn của nghiệp vụ vẫn dùng được — soát bằng B6.

### B5. Đặc tả dữ liệu + SQL + dữ liệu mẫu
Theo `examples/bm01-bm07/`: `make_data.py` (khai báo REPORTS, cột dataset), `samples.py` (trích số từ PDF,
`assert` số dòng), `outputs.py` (→ `Cau_truc_du_lieu.xlsx`, `Cau_truc_du_lieu_Oracle.sql`, `_samples/*.json|docx|pdf`),
`multi_data.py` (dữ liệu dạng dài + `mapping.json` cho multi_row).

### B6. Kiểm tra bằng engine thật
```bash
python3 check_template.py ../T.docx                                         # biến + danh sách dòng tXrY lặp được
python3 check_template.py ../T.docx --data ../_samples/BM01.json --pdf      # A
python3 check_template.py ../T.docx --mode multi_row --data rows.json --mapping mapping.json \
  --group-by ma_don_vi,tu_ngay,den_ngay --repeat t1r3:phan=A --repeat t2r3:phan=B --pdf          # B
python3 check_template.py ../T.docx --mode dashboard --data texts.json      # C
```
Đặt PDF điền thử cạnh PDF gốc: header, độ rộng cột, căn số, ngắt trang, tổng, khối ký.

### B7. Triển khai trên Superset
1. Team data tạo view theo SQL → khai báo dataset.
2. `/report-templates/` (Admin) → Upload .docx.
3. Tạo report: chọn dataset → mapping tự động; cấu hình định dạng (vi/date/custom) + aggregate (multi_row);
   Report mode = *Multiple rows*: chọn Group by, Repeat rows (`Table X, row Y`) + filter, Sort column.
4. Preview (lưu ý: preview chỉ lấy **5 dòng dữ liệu đầu** ⇒ multi_row thấy báo cáo chưa đủ dòng) → lưu → tải dữ liệu
   → chọn → Export PDF/ZIP.
5. Dashboard template: Publish → người dùng chọn ở *Download → Export dashboard / Export chart*.
Checklist bàn giao: `references/pitfalls.md`.

## Tài nguyên
- `scripts/sync_engine.py` — trích `rt_office/rt_format/rt_multi` (+ `dr_docx`) từ YAML → `customsso/`.
- `scripts/check_template.py` — kiểm tra/điền thử/PDF cho 3 chế độ bằng đúng code server.
- `scripts/pdf_probe.py` — dòng + toạ độ, gợi ý mép cột số.
- `scripts/docx_kit.js` — helper dựng docx.
- `examples/superset-values/` — 3 file Helm values mẫu (Report Builder, Dashboard Export, combined overlay).
- `examples/bm01-bm07/` — nguồn hoàn chỉnh 7 báo cáo + ví dụ multi_row (BM04M) + dashboard (DB01).
- `references/catalog.md` — PDF mẫu → template, số biến, grain, chế độ khuyến nghị.
