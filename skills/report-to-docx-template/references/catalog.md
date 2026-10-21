# Danh mục: báo cáo mẫu → template

PDF mẫu ở thư mục gốc dự án; template ở `Templates/`; nguồn dựng ở `Templates/_src/` (bản copy: `examples/bm01-bm07/`).

| PDF mẫu | Template | Chế độ hiện có | Khuyến nghị | Biến | Grain (1 báo cáo =) |
|---|---|---|---|---|---|
| `CDKT_TNH_24-12-2024.pdf` | BM01_Bang_can_doi_ke_toan_B02.docx | A per_row fixed | giữ A | 177 | 1 đơn vị × 1 tháng |
| `KQKD_TNH_24-12-2024.pdf` | BM02_Bao_cao_ket_qua_hoat_dong_B03.docx | A per_row fixed | giữ A | 78 | 1 đơn vị × 1 tháng |
| `PHAN TICH KQKD_TNH_24-12-2024.pdf` | BM03_Phan_tich_ket_qua_kinh_doanh_Bang13.docx | A per_row fixed | giữ A | 40 | 1 đơn vị × 1 khoảng ngày |
| `CDTKKT CAP III-CN Q3+PGD-31.07.2026.pdf` (F01/TCTD, có chi nhánh) | BM04_Bang_can_doi_tai_khoan_cap_III.docx / **BM04M_..._multi.docx** | A list cũ / **B** | B (BM04M) | 44 / 35 | 1 đơn vị × khoảng ngày × loại nguyên tệ |
| `CDTKKT_TNH_05.01.2024.pdf` (A01/TCTD, TT49, 14 trang, không chi nhánh) | dùng chung BM04/BM04M | như trên | B | — | `bieu_mau = A01/TCTD`, `can_cu_ban_hanh = Ban hành theo Thông tư 49/TT-NHNN ngày 31/12/2014`; `edges` ≈ 475, 565, 675, 780, 875, 975 |
| `408111009.pdf` | BM05_Bang_can_doi_ke_toan_TK_cap_4.docx | A list cũ | B: 1 dòng lặp, dòng chi nhánh là dữ liệu | 26 | 1 TK cấp 4 × khoảng ngày |
| `103699000.pdf` | BM06_Nhat_ky_so_cai_TK_cap_3.docx | A list cũ | B: dòng lặp + tổng `sum` | 26 | 1 TK cấp 3 × khoảng ngày |
| `1791182086662646.pdf` | BM07_Nhat_ky_quy_toan_chi_nhanh.docx | A list cũ | B: group_by gồm `loai_tien` | 18 | 1 đơn vị × ngày × loại tiền |
| — | DB01_Dashboard_template.docx (ví dụ) | C dashboard | — | 6 | 1 lần export dashboard |

Ghi chú:
- `template-a7f10f18-....docx` (hợp đồng tín dụng hạn mức) là template per_row gõ tay trong Word — dạng hợp đồng,
  dùng để tham khảo cách đặt token trong văn bản; soát tên biến bằng `check_template.py` trước khi dùng.
- Chuyển BM05–BM07 sang B: thay `listRow()` bằng `repeatRow()` với tên cột chi tiết (bỏ tiền tố `ct_`),
  view dạng dài như `data-contract.md` §3b; tổng dùng aggregate `sum` (sổ cái, nhật ký quỹ) hoặc cột tính sẵn.
