"""Sinh cấu trúc dữ liệu + dữ liệu mẫu cho các template Report Builder.

Đầu ra (thư mục Templates/):
  Cau_truc_du_lieu.xlsx          - đặc tả dataset (cột = biến template), bảng nguồn, dữ liệu mẫu
  Cau_truc_du_lieu_Oracle.sql    - DDL bảng nguồn + hàm định dạng số + view dataset cho Superset
  _samples/BMxx.json             - 1 dòng dataset mẫu (đúng như Superset trả về)
  _samples/BMxx_sample.docx/.pdf - template đã điền mẫu bằng chính engine rt_office.py
Chạy: python3 outputs.py  (cần build.js chạy trước để có rows.json)
"""
import json
from pathlib import Path

import samples as S

HERE = Path(__file__).parent
OUT = HERE.parent
SAMPLES = OUT / "_samples"
ROWS = json.loads((HERE / "rows.json").read_text())
AMT6 = ["dk_no", "dk_co", "ps_no", "ps_co", "ck_no", "ck_co"]
AMT6_DESC = ["Số dư đầu kỳ - Nợ", "Số dư đầu kỳ - Có", "Phát sinh trong kỳ - Nợ", "Phát sinh trong kỳ - Có",
             "Số dư cuối kỳ - Nợ", "Số dư cuối kỳ - Có"]


# ---------------------------------------------------------------- định dạng
def fmt(v, dec=0, neg="-"):
    """Mirror của hàm Oracle F_RPT_SO: 1234567.5 -> '1.234.567,50'; âm -> '-x' hoặc '(x)'; NULL -> ''."""
    if v is None:
        return ""
    s = f"{abs(v):,.{dec}f}".replace(",", "#").replace(".", ",").replace("#", ".")
    if v < 0:
        return f"({s})" if neg == "()" else f"-{s}"
    return s


def lines_of(values):
    return "\n".join("" if v is None else str(v) for v in values)


# ---------------------------------------------------------------- đặc tả
# Cột chung: (tên, kiểu dataset, mô tả, ví dụ)
SIGN = [
    ("ngay_ky", "VARCHAR2(2)", "Ngày ký (dd) - lấy từ NGAY_LAP", "24"),
    ("thang_ky", "VARCHAR2(2)", "Tháng ký (mm)", "12"),
    ("nam_ky", "VARCHAR2(4)", "Năm ký (yyyy)", "2024"),
    ("nguoi_lap", "VARCHAR2(100)", "Họ tên người lập bảng", "Nguyễn Văn A"),
    ("nguoi_kiem_soat", "VARCHAR2(100)", "Họ tên kiểm soát", "Trần Thị B"),
    ("lanh_dao", "VARCHAR2(100)", "Họ tên lãnh đạo ký", "Lê Văn C"),
]
BANK = ("ten_ngan_hang", "VARCHAR2(200)", "Tên ngân hàng in góc trái", "NGÂN HÀNG MẪU")
DVT = ("don_vi_tinh", "VARCHAR2(50)", "Đơn vị tính", "VN Đồng")

REPORTS = [
    dict(code="BM01", file="BM01_Bang_can_doi_ke_toan_B02.docx", name="Bảng cân đối kế toán (B02/TCTD)",
         kind="fixed", rows=ROWS["B02"], prefix="b02", neg="()",
         measures=[("tn", "thang_nay", "Tháng này"), ("tt", "thang_truoc", "Tháng trước")],
         keys=[("ma_don_vi", "VARCHAR2(20)", "Mã đơn vị (lọc)", "DV0001"), ("ky_bc", "VARCHAR2(7)", "Kỳ báo cáo MM/YYYY (lọc)", "12/2024")],
         header=[BANK, ("thang_bc", "VARCHAR2(7)", "Tháng báo cáo in trên tiêu đề (= KY_BC)", "12/2024"), DVT] + SIGN,
         grain="1 dòng = 1 đơn vị x 1 tháng"),
    dict(code="BM02", file="BM02_Bao_cao_ket_qua_hoat_dong_B03.docx", name="Báo cáo kết quả hoạt động (B03/TCTD)",
         kind="fixed", rows=ROWS["B03"], prefix="b03", neg="-",
         measures=[("tn", "thang_nay", "Tháng này"), ("tt", "thang_truoc", "Tháng trước"), ("lk", "luy_ke", "Lũy kế năm nay")],
         keys=[("ma_don_vi", "VARCHAR2(20)", "Mã đơn vị (lọc)", "DV0001"), ("ky_bc", "VARCHAR2(7)", "Kỳ báo cáo MM/YYYY (lọc)", "12/2024")],
         header=[BANK, ("thang_bc", "VARCHAR2(7)", "Tháng báo cáo in trên tiêu đề", "12/2024"), DVT] + SIGN,
         grain="1 dòng = 1 đơn vị x 1 tháng"),
    dict(code="BM03", file="BM03_Phan_tich_ket_qua_kinh_doanh_Bang13.docx", name="Bảng 13 - Phân tích kết quả kinh doanh",
         kind="fixed", rows=ROWS["BANG13"], prefix="b13", neg="-",
         measures=[("", "tang_giam", "Tăng/Giảm")],
         keys=[("ma_don_vi", "VARCHAR2(20)", "Mã đơn vị (lọc)", "DV0001")],
         header=[BANK, ("tu_ngay", "VARCHAR2(10)", "Từ ngày dd/mm/yyyy", "24/12/2024"),
                 ("den_ngay", "VARCHAR2(10)", "Đến ngày dd/mm/yyyy", "24/12/2024"), DVT] + SIGN,
         grain="1 dòng = 1 đơn vị x 1 khoảng ngày"),
    dict(code="BM04", file="BM04_Bang_can_doi_tai_khoan_cap_III.docx", name="Bảng cân đối tài khoản cấp III (F01/TCTD)",
         kind="list", grain="1 dòng = 1 đơn vị x 1 khoảng ngày x 1 loại nguyên tệ",
         keys=[("ma_don_vi", "VARCHAR2(20)", "Mã đơn vị (lọc)", "DV0311")],
         header=[BANK, ("ten_don_vi", "VARCHAR2(200)", "Tên đơn vị báo cáo", "Chi nhánh A + PGD trực thuộc"),
                 ("loai_nguyen_te", "VARCHAR2(50)", "Loại nguyên tệ", "Qui đổi"),
                 ("tu_ngay", "VARCHAR2(10)", "Từ ngày dd/mm/yyyy", "01/07/2026"), ("den_ngay", "VARCHAR2(10)", "Đến ngày dd/mm/yyyy", "31/07/2026"),
                 ("bieu_mau", "VARCHAR2(30)", "Mã biểu mẫu", "F01/TCTD"),
                 ("can_cu_ban_hanh", "VARCHAR2(200)", "Căn cứ ban hành", "Ban hành theo Thông tư 27/TT-NHNN ngày 31/12/2021"), DVT],
         sections=[("a", "A", "Phần A - TK trong bảng"), ("b", "B", "Phần B - TK ngoài bảng")],
         line_cols=[("ten_tk", "Tên tài khoản", "text", 48), ("tk_nhnn", "Số hiệu TK NHNN", "text", 10), ("tk_fcc", "Số hiệu TK FCC", "text", 12)]
         + [(f, d, "amount", None) for f, d in zip(AMT6, AMT6_DESC)]),
    dict(code="BM05", file="BM05_Bang_can_doi_ke_toan_TK_cap_4.docx", name="Bảng cân đối kế toán TK cấp 4",
         kind="list", grain="1 dòng = 1 tài khoản cấp 4 x 1 khoảng ngày",
         keys=[],
         header=[BANK, ("ma_tk", "VARCHAR2(20)", "Mã tài khoản cấp 4 (lọc)", "408111009"),
                 ("ten_tk", "VARCHAR2(200)", "Tên tài khoản", "Chi về nghiệp vụ ủy thác và đại lý"),
                 ("tu_ngay", "VARCHAR2(10)", "Từ ngày", "31/12/2024"), ("den_ngay", "VARCHAR2(10)", "Đến ngày", "31/12/2024"), DVT]),
    dict(code="BM06", file="BM06_Nhat_ky_so_cai_TK_cap_3.docx", name="Nhật ký sổ cái TK cấp 3 (BM-KT-046)",
         kind="list", grain="1 dòng = 1 tài khoản cấp 3 x 1 khoảng ngày",
         keys=[],
         header=[BANK, ("so_tk", "VARCHAR2(20)", "Số tài khoản cấp 3 (lọc)", "103699000"),
                 ("ten_tk", "VARCHAR2(200)", "Tên tài khoản cấp 3", "Các khoản phải thu khác"),
                 ("tu_ngay", "VARCHAR2(10)", "Từ ngày", "31/12/2002"), ("den_ngay", "VARCHAR2(10)", "Đến ngày", "31/12/2024"), DVT]),
    dict(code="BM07", file="BM07_Nhat_ky_quy_toan_chi_nhanh.docx", name="Nhật ký quỹ toàn chi nhánh",
         kind="list", grain="1 dòng = 1 đơn vị x 1 ngày số liệu x 1 loại tiền (nhiều loại tiền -> nhiều file, tải ZIP)",
         keys=[("ma_don_vi", "VARCHAR2(20)", "Mã đơn vị (lọc)", "DV0314")],
         header=[BANK, ("don_vi", "VARCHAR2(200)", "Tên đơn vị", "Ngân hàng mẫu - Chi nhánh A"),
                 ("ngay_so_lieu", "VARCHAR2(10)", "Ngày số liệu dd/mm/yyyy (lọc)", "10/11/2026"),
                 ("ngay_tao", "VARCHAR2(20)", "Thời điểm tạo báo cáo dd/mm/yyyy hh24:mi", "05/10/2026 13:24"),
                 ("loai_tien", "VARCHAR2(3)", "Mã loại tiền (lọc)", "USD"),
                 ("du_dau_ky", "VARCHAR2(30)", "Dư đầu kỳ (đã định dạng)", "0,00"),
                 ("tong_thu", "VARCHAR2(30)", "Tổng thu", "17.015.200,00"),
                 ("tong_chi", "VARCHAR2(30)", "Tổng chi", "15.100,00"),
                 ("du_cuoi_ky", "VARCHAR2(30)", "Dư cuối kỳ", "17.000.100,00"),
                 ("thu_quy", "VARCHAR2(100)", "Họ tên thủ quỹ", "Phạm Thị D"),
                 ("ke_toan_quy", "VARCHAR2(100)", "Họ tên P. Kế toán & Quỹ", "Hoàng Văn E"),
                 ("tong_giam_doc", "VARCHAR2(100)", "Họ tên Tổng giám đốc", "Đỗ Văn F")]),
]
for r in REPORTS[3:6]:
    r["header"] = r["header"] + SIGN


# ---------------------------------------------------------------- dataset spec (cột = biến)
def dataset_columns(r):
    """[(tên cột, kiểu, mô tả, quy tắc)] theo đúng thứ tự xuất hiện; khóa lọc đứng đầu."""
    cols = [(n, t, d, "Khóa lọc (không in)") for n, t, d, _ in r["keys"]]
    cols += [(n, t, d, "") for n, t, d, _ in r["header"]]
    if r["kind"] == "fixed":
        neg = "số âm trong ngoặc (x)" if r["neg"] == "()" else "số âm có dấu -"
        for i, (stt, label, _) in enumerate(r["rows"]):
            for suf, _, mlabel in r["measures"]:
                name = f"{r['prefix']}_r{i + 1:02d}" + (f"_{suf}" if suf else "")
                cols.append((name, "VARCHAR2(30)", f"[{stt}] {label} - {mlabel}", f"Số đã định dạng #.###; {neg}"))
    elif r["code"] == "BM04":
        for p, P, plabel in r["sections"]:
            for f, d, typ, mx in r["line_cols"]:
                rule = f"Nhiều dòng (\\n); cắt tối đa {mx} ký tự" if typ == "text" else "Nhiều dòng (\\n); số đã định dạng"
                cols.append((f"{p}_{f}", "CLOB", f"{plabel}: {d}", rule))
            for f, d in zip(AMT6, AMT6_DESC):
                cols.append((f"tong_{p}_{f}", "VARCHAR2(30)", f"{plabel}: Tổng cộng - {d}", "Số đã định dạng"))
    elif r["code"] == "BM05":
        cols.append(("ct_loai_tien", "CLOB", "Cột 'Chi nhánh / Loại tiền': dòng tiêu đề chi nhánh 'mã - tên', tiếp theo là các dòng loại tiền", "Nhiều dòng; tối đa 40 ký tự"))
        cols += [(f"ct_{f}", "CLOB", d, "Nhiều dòng; dòng tiêu đề chi nhánh để trống") for f, d in zip(AMT6, AMT6_DESC)]
        cols.append(("tc_loai_tien", "CLOB", "Nhãn dòng tổng theo loại tiền: 'Tổng cộng VND'...", "Nhiều dòng (1 dòng / loại tiền)"))
        cols += [(f"tc_{f}", "CLOB", f"Tổng cộng - {d}", "Nhiều dòng (1 dòng / loại tiền)") for f, d in zip(AMT6, AMT6_DESC)]
    elif r["code"] == "BM06":
        cols.append(("ct_so_tk", "CLOB", "Số tài khoản chi tiết", "Nhiều dòng"))
        cols.append(("ct_ten_tk", "CLOB", "Tên tài khoản chi tiết", "Nhiều dòng; cắt tối đa 52 ký tự"))
        cols += [(f"ct_{f}", "CLOB", d, "Nhiều dòng; NULL -> dòng trống") for f, d in zip(AMT6, AMT6_DESC)]
        cols += [(f"tong_{f}", "VARCHAR2(30)", f"Tổng cộng - {d}", "Số đã định dạng") for f, d in zip(AMT6, AMT6_DESC)]
    elif r["code"] == "BM07":
        for f, d, mx in [("so_ct", "Số chứng từ", 20), ("dien_giai", "Diễn giải", 50), ("tien_thu", "Tiền thu", None),
                         ("tien_chi", "Tiền chi", None), ("giao_dich_vien", "Giao dịch viên", 32), ("so_ct_gdv", "Số C.Từ theo GDV", 20)]:
            cols.append((f"ct_{f}", "CLOB", d, f"Nhiều dòng; cắt tối đa {mx} ký tự" if mx else "Nhiều dòng; số đã định dạng (VND 0 số lẻ, ngoại tệ 2)"))
    return cols


# ---------------------------------------------------------------- dữ liệu mẫu (1 dòng dataset)
def base_values(r):
    return {n: ex for n, _, _, ex in r["keys"] + r["header"]}


def sample_row(r):
    v = base_values(r)
    if r["kind"] == "fixed":
        data = {"BM01": S.b02, "BM02": S.b03, "BM03": S.b13}[r["code"]](len(r["rows"]))
        for i, vals in enumerate(data):
            for (suf, _, _), x in zip(r["measures"], vals):
                v[f"{r['prefix']}_r{i + 1:02d}" + (f"_{suf}" if suf else "")] = fmt(x, 0, r["neg"])
        return v, data
    if r["code"] == "BM04":
        data, totals = S.cdtk3()
        for p, _, _ in r["sections"]:
            for f, _, typ, mx in r["line_cols"]:
                vals = [(row[f] or "")[:mx] if typ == "text" else fmt(row[f]) for row in data[p]]
                v[f"{p}_{f}"] = lines_of(vals)
            for f, x in zip(AMT6, totals[p]):
                v[f"tong_{p}_{f}"] = fmt(x)
        return v, data
    if r["code"] == "BM05":
        out = []
        for cn in dict.fromkeys(x["ma_cn"] for x in S.TK4):
            rows = [x for x in S.TK4 if x["ma_cn"] == cn]
            out.append({"nhan": f"{cn} - {rows[0]['ten_cn']}", **{f: None for f in AMT6}})
            out += [{"nhan": x["loai_tien"], **{f: x[f] for f in AMT6}} for x in rows]
        v["ct_loai_tien"] = lines_of(x["nhan"][:40] for x in out)
        for f in AMT6:
            v[f"ct_{f}"] = lines_of(fmt(x[f]) for x in out)
        currencies = sorted({x["loai_tien"] for x in S.TK4})
        v["tc_loai_tien"] = lines_of(f"Tổng cộng {c}" for c in currencies)
        for f in AMT6:
            v[f"tc_{f}"] = lines_of(fmt(sum(x[f] for x in S.TK4 if x["loai_tien"] == c)) for c in currencies)
        return v, S.TK4
    if r["code"] == "BM06":
        data = S.nksc()
        v["ct_so_tk"] = lines_of(x["so_tk"] for x in data)
        v["ct_ten_tk"] = lines_of(x["ten_tk"][:52] for x in data)
        for f in AMT6:
            v[f"ct_{f}"] = lines_of(fmt(x[f]) for x in data)
            v[f"tong_{f}"] = fmt(sum(x[f] or 0 for x in data))
        return v, data
    if r["code"] == "BM07":
        keys = ["so_ct", "dien_giai", "tien_thu", "tien_chi", "giao_dich_vien", "so_ct_gdv"]
        data = [dict(zip(keys, t)) for t in S.NKQ_USD]
        for k in keys:
            v[f"ct_{k}"] = lines_of(fmt(x[k], 2) if k.startswith("tien") else x[k] for x in data)
        v.update({k: fmt(x, 2) for k, x in S.NKQ_USD_SUM.items()})
        return v, data
    raise ValueError(r["code"])


# ---------------------------------------------------------------- bảng nguồn (đề xuất cho team data)
def source_tables(r):
    """[(bảng, cột, kiểu, khóa?, mô tả)]"""
    c, t = r["code"], f"RPT_{r['code']}"
    sign_src = [("ngay_lap", "DATE", "", "Ngày lập/ký báo cáo"), ("nguoi_lap", "VARCHAR2(100)", "", "Người lập"),
                ("nguoi_kiem_soat", "VARCHAR2(100)", "", "Kiểm soát"), ("lanh_dao", "VARCHAR2(100)", "", "Lãnh đạo")]
    if r["kind"] == "fixed":
        k = [("ma_don_vi", "VARCHAR2(20)", "PK", "Mã đơn vị")]
        k += [("ky_bc", "VARCHAR2(7)", "PK", "Kỳ MM/YYYY")] if c != "BM03" else [("tu_ngay", "DATE", "PK", "Từ ngày"), ("den_ngay", "DATE", "PK", "Đến ngày")]
        hdr = k + [("ten_ngan_hang", "VARCHAR2(200)", "", "Tên ngân hàng"), ("don_vi_tinh", "VARCHAR2(50)", "", "Đơn vị tính")] + sign_src
        ct = k + [("ma_chi_tieu", "VARCHAR2(10)", "PK", f"Mã dòng chỉ tiêu: {r['prefix']}_r01..{r['prefix']}_r{len(r['rows']):02d} (xem danh mục)"),
                  ("ten_chi_tieu", "VARCHAR2(300)", "", "Tên chỉ tiêu (tham khảo)")]
        ct += [(src, "NUMBER(25,2)", "", lbl) for _, src, lbl in r["measures"]]
        return [(f"{t}_HDR", *x) for x in hdr] + [(f"{t}_CT", *x) for x in ct]
    if c == "BM04":
        k = [("ma_don_vi", "VARCHAR2(20)", "PK", "Mã đơn vị"), ("tu_ngay", "DATE", "PK", "Từ ngày"), ("den_ngay", "DATE", "PK", "Đến ngày"),
             ("loai_nguyen_te", "VARCHAR2(50)", "PK", "Loại nguyên tệ (Qui đổi / VND / USD...)")]
        hdr = k + [("ten_ngan_hang", "VARCHAR2(200)", "", ""), ("ten_don_vi", "VARCHAR2(200)", "", ""), ("bieu_mau", "VARCHAR2(30)", "", ""),
                   ("can_cu_ban_hanh", "VARCHAR2(200)", "", ""), ("don_vi_tinh", "VARCHAR2(50)", "", "")]
        hdr += [(f"tong_{p}_{f}", "NUMBER(25,2)", "", f"Tổng cộng phần {P} - {d}") for p, P, _ in r["sections"] for f, d in zip(AMT6, AMT6_DESC)] + sign_src
        ct = k + [("phan", "CHAR(1)", "PK", "A = trong bảng, B = ngoài bảng"), ("stt", "NUMBER(6)", "PK", "Thứ tự in"),
                  ("ten_tk", "VARCHAR2(300)", "", "Tên tài khoản / tên đơn vị (dòng chi tiết chi nhánh)"),
                  ("tk_nhnn", "VARCHAR2(10)", "", "Số hiệu TK NHNN"), ("tk_fcc", "VARCHAR2(12)", "", "Số hiệu TK FCC/T24")]
        ct += [(f, "NUMBER(25,2)", "", d) for f, d in zip(AMT6, AMT6_DESC)]
        return [(f"{t}_HDR", *x) for x in hdr] + [(f"{t}_CT", *x) for x in ct]
    if c in ("BM05", "BM06"):
        kcol = "ma_tk" if c == "BM05" else "so_tk"
        k = [(kcol, "VARCHAR2(20)", "PK", "Tài khoản"), ("tu_ngay", "DATE", "PK", "Từ ngày"), ("den_ngay", "DATE", "PK", "Đến ngày")]
        hdr = k + [("ten_tk", "VARCHAR2(200)", "", "Tên tài khoản"), ("ten_ngan_hang", "VARCHAR2(200)", "", ""), ("don_vi_tinh", "VARCHAR2(50)", "", "")] + sign_src
        if c == "BM05":
            ct = k + [("ma_cn", "VARCHAR2(10)", "PK", "Mã chi nhánh"), ("ten_cn", "VARCHAR2(200)", "", "Tên chi nhánh"), ("loai_tien", "VARCHAR2(3)", "PK", "Loại tiền")]
        else:
            ct = k + [("so_tk_ct", "VARCHAR2(20)", "PK", "Số tài khoản chi tiết"), ("ten_tk_ct", "VARCHAR2(200)", "", "Tên tài khoản chi tiết")]
        ct += [(f, "NUMBER(25,2)", "", d) for f, d in zip(AMT6, AMT6_DESC)]
        return [(f"{t}_HDR", *x) for x in hdr] + [(f"{t}_CT", *x) for x in ct]
    k = [("ma_don_vi", "VARCHAR2(20)", "PK", "Mã đơn vị"), ("ngay_so_lieu", "DATE", "PK", "Ngày số liệu"), ("loai_tien", "VARCHAR2(3)", "PK", "Loại tiền")]
    hdr = k + [("ten_ngan_hang", "VARCHAR2(200)", "", ""), ("don_vi", "VARCHAR2(200)", "", "Tên đơn vị"), ("ngay_tao", "DATE", "", "Thời điểm tạo"),
               ("du_dau_ky", "NUMBER(25,2)", "", "Dư đầu kỳ"), ("tong_thu", "NUMBER(25,2)", "", "Tổng thu"),
               ("tong_chi", "NUMBER(25,2)", "", "Tổng chi"), ("du_cuoi_ky", "NUMBER(25,2)", "", "Dư cuối kỳ"),
               ("thu_quy", "VARCHAR2(100)", "", ""), ("ke_toan_quy", "VARCHAR2(100)", "", ""), ("tong_giam_doc", "VARCHAR2(100)", "", "")]
    ct = k + [("stt", "NUMBER(6)", "PK", "Thứ tự in"), ("so_ct", "VARCHAR2(30)", "", "Số chứng từ"), ("dien_giai", "VARCHAR2(500)", "", "Diễn giải"),
              ("tien_thu", "NUMBER(25,2)", "", "Tiền thu"), ("tien_chi", "NUMBER(25,2)", "", "Tiền chi"),
              ("giao_dich_vien", "VARCHAR2(100)", "", "Tên giao dịch viên"), ("so_ct_gdv", "VARCHAR2(50)", "", "Số chứng từ theo GDV")]
    return [(f"{t}_HDR", *x) for x in hdr] + [(f"{t}_CT", *x) for x in ct]
