# Phân tích bố cục & pattern template

## 1. Đọc báo cáo mẫu (checklist)
| Hạng mục | Lấy từ đâu | Ghi chú |
|---|---|---|
| Khổ / hướng | `pdf_probe.py` dòng đầu (`1008x792` = ngang, `612x792` = dọc) | Template luôn A4; ngang khi ≥ 7 cột số |
| Header trái | tên ngân hàng, đơn vị, logo | `pageHeader({ left, logo })` |
| Header giữa | tiêu đề, kỳ, loại nguyên tệ | `title`, `sub` |
| Header phải | biểu mẫu số, căn cứ ban hành, đơn vị tính, "Trang x/y" | `right`; số trang tự sinh |
| Cột bảng | toạ độ x các nhãn cột, cột 2 tầng (Số dư đầu kỳ → Nợ/Có) | `H(..., {span:2})` + `noCo()` |
| Dòng | cố định hay thay đổi theo dữ liệu | quyết định pattern |
| Kiểu dòng | đậm (tiêu đề nhóm), thường, thụt lề/nghiêng (chi tiết) | `H/B/N/S` trong `rows.js` |
| Dòng tổng | "Tổng cộng", tổng theo loại tiền | `totalRow()` hoặc dòng riêng |
| Khối ký | chức danh, có dòng "Ngày ... tháng ... năm" không | `SIGN_STD` / `signatures()` |
| Số | phân cách nghìn `.`, thập phân `,`, âm `(x)` hay `-x`, số lẻ (VND 0, ngoại tệ 2) | xử lý ở SQL `F_RPT_SO` |
| Lỗi nguồn | font hỏng (VD tên GDV nhật ký quỹ), Unicode NFD | chuẩn hoá NFC; nhập tay dữ liệu mẫu nếu cần |

## 2. Bảng quyết định pattern
| Dấu hiệu | Loại / pattern | Biến | Ví dụ |
|---|---|---|---|
| Danh mục chỉ tiêu theo thông tư, không đổi | **A per_row – fixed** | `<prefix>_rNN_<đo>` mỗi ô | BM01 (B02), BM02 (B03), BM03 (Bảng 13) |
| Số dòng phụ thuộc dữ liệu | **B multi_row – repeat** (khuyến nghị) | token đơn trong 1 dòng lặp: `{#ten_tk#}`, `{#dk_no#}` | BM04M; áp dụng cho BM04–BM07 |
| List chia phần A/B | B: mỗi phần 1 bảng, mỗi bảng 1 dòng lặp + filter `phan = A/B` | tổng phần: `tong_a_*` (cột dataset, `first`) | BM04M |
| List có dòng nhóm (chi nhánh) xen chi tiết | B: 2 dòng lặp liền nhau? **Không** – engine chèn hết bản sao của dòng 1 rồi mới tới dòng 2. Dùng 1 dòng lặp, dòng nhóm là 1 dòng dữ liệu có ô số rỗng (sort_key đặt trước chi tiết) | | BM05 |
| Nhiều loại tiền, mỗi loại 1 file | group_by gồm `loai_tien` | | BM07 |
| Bắt buộc 1 dòng dataset = 1 file mà vẫn là list | A per_row – list cũ: biến nhiều dòng `\n` + `listRow()` | `ct_<cột>` | BM04–BM07 bản per_row |
| Khung Word bọc dashboard/chart | **C dashboard** | `{#dashboard#}`, `{#datetime#}`, text | DB01 |
| > 200 ô cố định | tách template, hoặc chuyển phần dài sang B | | |

Đếm biến trước khi dựng: fixed = `số dòng × số cột đo + header + ký`; BM01 = 85×2 + 7 = 177/200.
multi_row đếm theo tên biến khác nhau (dòng lặp A và B dùng chung tên ⇒ BM04M chỉ 35 biến).

## 3. Pattern B – dòng lặp thật (multi_row)
```
t1r1  | Tên TK | TK NHNN | TK FCC | Số dư đầu kỳ (span 2) | ...   <- hdr() tableHeader: lặp mỗi trang, có rowSpan OK
t1r2  |        |         |        | Nợ | Có | ...                 <- noCo()
t1r3  | {#ten_tk#} | {#tk_nhnn#} | {#tk_fcc#} | {#dk_no#} | ...  <- repeatRow(): engine clone cho mỗi dòng dữ liệu
t1r4  | Tổng cộng: | {#tong_a_dk_no#} | ...                      <- totalRow(): biến chung (aggregate)
```
- Dòng lặp: không rowSpan/vMerge, không `tableHeader`, không ảnh/bookmark; `cantSplit` được.
- Tên dài **được** tự xuống dòng (mỗi dòng dữ liệu là 1 dòng bảng riêng) ⇒ không cần cắt `SUBSTR` như pattern cũ.
- Thứ tự dòng = thứ tự query (1 cột sort) ⇒ cột `sort_key` (vd `phan || LPAD(stt, 6, '0')`).
- ID `tXrY` đếm theo bảng trong thân văn bản theo thứ tự xuất hiện; chạy `check_template.py T.docx` để xem danh sách.
- Tổng toàn group: aggregate `sum` trên chính cột chi tiết; tổng theo phần/loại: cột dataset tính sẵn + `first`.

## 3b. Pattern list cũ trên per_row (không có vòng lặp)
Một dòng bảng duy nhất, mỗi ô chứa 1 biến nhiều dòng:
```
| {#ct_so_tk#} | {#ct_ten_tk#} | {#ct_dk_no#} | ... |      <- listRow(): cantSplit=false, cỡ chữ 7.5pt, canh trên
| Tổng cộng                   | {#tong_dk_no#} | ... |   <- totalRow()
```
Quy tắc để các cột **thẳng hàng**:
1. Mọi cột của cùng bảng có **cùng số dòng, cùng thứ tự** (giá trị rỗng vẫn là 1 dòng trống: `NULL → ''` rồi nối `\n`).
2. Không dòng nào tự wrap ⇒ cắt chữ theo bề rộng cột: `SUBSTR(ten, 1, N)`.
   N ≈ `bề rộng cột (twip) / 20 / (cỡ chữ pt × 0.5)`; vd cột 4100 twip, 7.5pt → ~52 ký tự (BM06).
   Đã dùng: BM04 tên TK 48, BM06 52, BM07 diễn giải 50 / GDV 32.
3. Header bảng `tableHeader: true` ⇒ lặp mỗi trang; dòng list cho phép ngắt trang.
Giới hạn 50.000 ký tự/giá trị (BM04 thực tế 14.310); vượt thì tách dataset.

## 3c. Pattern C – dashboard
- `para(T('dashboard'))` là đoạn riêng trong thân; trước/sau là tiêu đề, `TP. HCM, {#datetime#}`, khối ký.
- Section 1 cột; khổ/lề của section quyết định bề rộng bảng chart. Không đặt `{#dashboard#}` trong bảng/header.

## 4. Kích thước & quy đổi
- 1 pt = 20 twip; 1 inch = 1440 twip. A4 = 11906 × 16838 twip. Lề 720 (0.5").
- Vùng in: dọc `PORTRAIT_W = 10466`, ngang `LANDSCAPE_W = 15398`.
- Độ rộng cột: lấy khoảng cách x giữa các mép cột trong PDF, chia tỉ lệ cho đủ vùng in. Tổng `W[]` = vùng in.
  Ví dụ BM04 (ngang): `[3550, 950, 1000, 1650×5, 1648]` = 15398.
- Font Times New Roman 10pt (bảng cố định), 7.5pt (dòng list), tiêu đề 14pt đậm.

## 5. Header / ký / trang
- `pageHeader` là bảng 3 cột không viền trong Header Word ⇒ lặp mọi trang, biến trong header vẫn được điền.
- `signatures(width, titles, names, withDate)` — `keepNext` mọi dòng để khối ký không bị tách khỏi dòng cuối.
- Số trang `Trang x/y` dùng field Word (LibreOffice tự tính khi xuất PDF).

## 6. Map 7 báo cáo đã làm
| Mã | Báo cáo | Pattern | Khổ | Đặc thù |
|---|---|---|---|---|
| BM01 | CĐKT B02/TCTD | fixed 85 dòng × (tháng này, tháng trước) | dọc | âm trong ngoặc `(x)` |
| BM02 | KQKD B03/TCTD | fixed 23 × 3 (tháng này, trước, lũy kế) | dọc | âm `-x` |
| BM03 | Phân tích KQKD Bảng 13 | fixed 30 × 1 | dọc | STT 1..30, dòng in đậm theo tên |
| BM04 | CĐTK cấp III (F01/A01) | list 2 phần A/B + tổng | ngang | `bieu_mau`, `can_cu_ban_hanh` là biến |
| BM04M | CĐTK cấp III – multi_row | 2 bảng, dòng lặp t1r3 (A), t2r3 (B) | ngang | ví dụ chế độ B |
| DB01 | Khung dashboard | `{#dashboard#}` | dọc | ví dụ chế độ C |
| BM05 | CĐKT TK cấp 4 | list có dòng nhóm chi nhánh + tổng theo loại tiền | ngang | 2 view phụ `_DONG`, `_TONG` |
| BM06 | Nhật ký sổ cái TK cấp 3 | list + tổng | ngang | |
| BM07 | Nhật ký quỹ toàn chi nhánh | list + 4 dòng dư/thu/chi | ngang | logo, 1 file / loại tiền, 2 số lẻ ngoại tệ |
