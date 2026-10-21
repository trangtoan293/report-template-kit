# Hợp đồng dữ liệu: biến template ↔ dataset Superset

## 1. Nguyên tắc
1. **Tên cột view = tên biến** (snake_case, không dấu). Report Builder auto-map, không cần map tay.
2. **1 dòng view = 1 file in**. Ghi rõ grain: "1 dòng = 1 đơn vị × 1 tháng", "... × 1 loại tiền".
3. Cột **khoá lọc** (ma_don_vi, ky_bc...) có trong view nhưng không in — dùng để filter khi tạo report.
4. Định dạng: **hoặc** trả số/ngày thô và cấu hình định dạng ở mapping (`vi`, `date`, `custom` — bắt buộc khi
   dùng aggregate), **hoặc** trả chuỗi đã định dạng sẵn (`F_RPT_SO`, `TO_CHAR`) và để mapping `raw`.
   Bộ BM01–BM07 per_row dùng cách định dạng trong SQL; BM04M multi_row dùng định dạng ở mapping.
5. Bảng nguồn `RPT_BMxx_HDR` (1 dòng/file) + `RPT_BMxx_CT` (chi tiết) là **đề xuất**; team data dựng khác cũng được,
   miễn view cuối trả đúng tên cột.

## 2. Quy ước tên biến
| Nhóm | Tên | Ghi chú |
|---|---|---|
| Header chung | `ten_ngan_hang`, `ten_don_vi`/`don_vi`, `don_vi_tinh`, `bieu_mau`, `can_cu_ban_hanh` | |
| Kỳ | `thang_bc` (MM/YYYY), `tu_ngay`, `den_ngay`, `ngay_so_lieu` (dd/mm/yyyy), `ngay_tao` | |
| Khối ký | `ngay_ky`, `thang_ky`, `nam_ky`, `nguoi_lap`, `nguoi_kiem_soat`, `lanh_dao` | từ `ngay_lap` |
| Fixed | `<prefix>_rNN_<đo>`: `b02_r05_tn`, `b03_r17_lk`, `b13_r30` | NN = thứ tự dòng trong `rows.js`, 2 chữ số |
| Đo | `tn` tháng này, `tt` tháng trước, `lk` lũy kế | |
| 6 cột KT | `dk_no dk_co ps_no ps_co ck_no ck_co` | đầu kỳ / phát sinh / cuối kỳ × Nợ/Có |
| List | `ct_<cột>` chi tiết, `tong_<cột>` tổng; phần A/B: `a_<cột>`, `tong_a_<cột>` | cột list cùng tiền tố phải cùng số dòng |

Khi bổ sung dòng chỉ tiêu ở **giữa** danh mục fixed, mã `rNN` phía sau bị dời ⇒ cập nhật đồng thời template, view
và mapping `ma_chi_tieu`. Thêm ở cuối thì an toàn.

## 3. SQL Oracle cho per_row (sinh bởi outputs.py)
### Định dạng số
```sql
CREATE OR REPLACE FUNCTION F_RPT_SO(p_so NUMBER, p_so_le NUMBER DEFAULT 0, p_am VARCHAR2 DEFAULT '-')
RETURN VARCHAR2 DETERMINISTIC IS
  v VARCHAR2(60);
BEGIN
  IF p_so IS NULL THEN RETURN NULL; END IF;
  v := TO_CHAR(ABS(p_so), 'FM999G999G999G999G999G990' || CASE WHEN p_so_le > 0 THEN 'D' || RPAD('0', p_so_le, '0') END,
               'NLS_NUMERIC_CHARACTERS='',.''');
  IF p_so < 0 THEN RETURN CASE p_am WHEN '()' THEN '(' || v || ')' ELSE '-' || v END; END IF;
  RETURN v;
END;
```
`F_RPT_SO(-1234567.5, 2, '()')` → `(1.234.567,50)`. Mirror Python: `fmt()` trong `make_data.py`.

### Fixed → pivot
```sql
SELECT ..., p.b02_r01_tn, ...
FROM RPT_BM01_HDR h
LEFT JOIN (SELECT ma_don_vi, ky_bc,
             MAX(CASE WHEN ma_chi_tieu = 'b02_r01' THEN F_RPT_SO(thang_nay, 0, '()') END) AS b02_r01_tn, ...
           FROM RPT_BM01_CT GROUP BY ma_don_vi, ky_bc) p ON p.ma_don_vi = h.ma_don_vi AND p.ky_bc = h.ky_bc;
```

### List → nối dòng
`LISTAGG` giới hạn 4000 byte ⇒ dùng XMLAGG trả CLOB:
```sql
(SELECT RTRIM(DBMS_XMLGEN.CONVERT(XMLAGG(XMLELEMENT(e, SUBSTR(c.ten_tk,1,48) || CHR(10)) ORDER BY c.stt)
        .EXTRACT('//text()').getClobVal(), 1), CHR(10))
   FROM RPT_BM04_CT c WHERE c.ma_don_vi = h.ma_don_vi AND ... AND c.phan = 'A') AS a_ten_tk
```
- Cùng `ORDER BY` cho mọi cột của 1 bảng. `NULL` → `F_RPT_SO` trả NULL → `XMLELEMENT` vẫn sinh `CHR(10)` ⇒ giữ dòng trống.
- PostgreSQL: `string_agg(expr, E'\n' ORDER BY ...)` và `to_char` tương đương.
- Nếu driver trả CLOB không phải chuỗi: `MAX_STRING_SIZE=EXTENDED` + `LISTAGG` (≤ 32767 byte).

### Dòng nhóm xen chi tiết (BM05)
View phụ `UNION ALL` dòng tiêu đề nhóm (`thu_tu = 0`, ô số NULL) với dòng chi tiết (`thu_tu = 1`), rồi XMLAGG
`ORDER BY ma_cn, thu_tu, nhan`. Tổng theo loại tiền: view `GROUP BY loai_tien` riêng.

## 3b. Dataset dạng dài cho multi_row (loại B)
1 dòng view = 1 dòng chi tiết. Cột gồm: **khoá group** + **header lặp lại** (giống nhau trong group) + **chi tiết** +
`sort_key` + (tuỳ chọn) cột lọc dòng lặp (`phan`) + cột tổng theo phần.
```sql
CREATE OR REPLACE VIEW V_RPT_BM04M AS
SELECT h.ma_don_vi, TO_CHAR(h.tu_ngay,'DD/MM/YYYY') tu_ngay, TO_CHAR(h.den_ngay,'DD/MM/YYYY') den_ngay,
       h.loai_nguyen_te, h.ten_ngan_hang, h.ten_don_vi, h.bieu_mau, h.can_cu_ban_hanh, h.don_vi_tinh,
       TO_CHAR(h.ngay_lap,'DD') ngay_ky, TO_CHAR(h.ngay_lap,'MM') thang_ky, TO_CHAR(h.ngay_lap,'YYYY') nam_ky,
       h.nguoi_lap, h.nguoi_kiem_soat, h.lanh_dao,
       c.phan, c.phan || LPAD(c.stt, 6, '0') AS sort_key,
       c.ten_tk, c.tk_nhnn, c.tk_fcc, c.dk_no, c.dk_co, c.ps_no, c.ps_co, c.ck_no, c.ck_co,      -- số THÔ
       SUM(CASE WHEN c.phan = 'A' THEN c.dk_no END) OVER (PARTITION BY c.ma_don_vi, c.tu_ngay, c.den_ngay, c.loai_nguyen_te) AS tong_a_dk_no
       -- ... tương tự 11 cột tong_a_*/tong_b_* còn lại
FROM RPT_BM04_HDR h JOIN RPT_BM04_CT c
  ON c.ma_don_vi = h.ma_don_vi AND c.tu_ngay = h.tu_ngay AND c.den_ngay = h.den_ngay AND c.loai_nguyen_te = h.loai_nguyen_te;
```
Cấu hình report (UI hoặc `--mapping` khi kiểm tra local, ví dụ `_samples/BM04M_mapping.json`):
| Mục | Giá trị |
|---|---|
| Report mode | Multiple rows |
| Group by | `ma_don_vi, tu_ngay, den_ngay, loai_nguyen_te` |
| Repeat rows | `t1r3` filter `phan = A`; `t2r3` filter `phan = B` |
| Sort | `sort_key` tăng dần |
| `dk_no … ck_co` | number_format `vi`, decimals 0 |
| `tong_a_*`, `tong_b_*` | aggregate `first`, `vi` 0 |
| header, ký | aggregate `constant` (mặc định) |

Lưu ý: tổng của **cả group** thì dùng thẳng aggregate `sum` trên cột chi tiết (khỏi cần cột tổng);
khi dòng lặp có filter, tổng theo filter phải tính sẵn trong view (aggregate không biết filter).
Số dư Có hiển thị `(x)`: custom number `#.##0;(#.##0)`.

## 4. File đặc tả Excel (`Cau_truc_du_lieu.xlsx`)
Sheet `Huong_dan`, `Tong_quan`, và với mỗi BM: `_Dataset` (STT, cột = biến, kiểu, mô tả, quy tắc, giá trị mẫu),
`_Nguon` (bảng nguồn đề xuất), `_Mau` (dữ liệu chi tiết trích từ PDF). Đây là tài liệu bàn giao cho team data.

## 5. Dữ liệu mẫu
`_samples/BMxx.json` = đúng 1 dòng Superset sẽ trả (dict tên cột → chuỗi). Dùng cho `check_template.py --data`
và để team data so sánh output view của họ.
