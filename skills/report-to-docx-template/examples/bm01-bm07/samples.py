"""Trích dữ liệu mẫu từ các PDF báo cáo gốc -> dữ liệu chi tiết (dạng bảng, số là number)."""
import re
import unicodedata
from pathlib import Path

import fitz

SRC = Path(__file__).resolve().parents[2]
NUM = re.compile(r"^\(?-?[\d.]+\)?$")


def to_num(s):
    neg = s.startswith("(") or s.startswith("-")
    v = int(s.strip("()-").replace(".", ""))
    return -v if neg else v


def is_amount(s):
    return bool(NUM.match(s)) and ("." in s or s.strip("()-") == "0")


def lines(page, tol=2.5):
    # PDF gốc dùng Unicode tổ hợp (NFD) -> chuẩn hoá NFC để so khớp chuỗi
    ws = sorted(((*w[:4], unicodedata.normalize("NFC", w[4])) for w in page.get_text("words")), key=lambda w: (round(w[1]), w[0]))
    out = []
    for w in ws:
        if out and abs(out[-1][0] - w[1]) < tol:
            out[-1][1].append(w)
        else:
            out.append([w[1], [w]])
    return [(y, sorted(ws_, key=lambda w: w[0])) for y, ws_ in out]


def by_right_edge(words, edges):
    """Gán từng số vào cột có mép phải gần nhất."""
    vals = [None] * len(edges)
    for w in words:
        if is_amount(w[4]):
            i = min(range(len(edges)), key=lambda k: abs(edges[k] - w[2]))
            vals[i] = to_num(w[4])
    return vals


def fixed_values(pdf, n_expected, edges, label_max_x):
    rows = []
    for page in fitz.open(SRC / pdf):
        for _, ws in lines(page):
            amounts = [w for w in ws if w[0] > label_max_x and is_amount(w[4])]
            if amounts:
                rows.append(by_right_edge(amounts, edges))
    assert len(rows) == n_expected, f"{pdf}: {len(rows)} != {n_expected}"
    return rows


def b02(n):
    return fixed_values("CDKT_TNH_24-12-2024.pdf", n, [636, 785], 500)


def b03(n):
    return fixed_values("KQKD_TNH_24-12-2024.pdf", n, [392, 491, 594], 300)


def b13(n):
    return fixed_values("PHAN TICH KQKD_TNH_24-12-2024.pdf", n, [545], 400)


def cdtk3():
    """Bảng cân đối TK cấp III có chi nhánh (27 trang). Trả về {'a': [...], 'b': [...]}, tổng."""
    edges = [477, 567, 675, 783, 886, 981]
    data, totals, section = {"a": [], "b": []}, {}, "a"
    for page in fitz.open(SRC / "CDTKKT CAP III-CN Q3+PGD-31.07.2026.pdf"):
        for y, ws in lines(page):
            text = " ".join(w[4] for w in ws)
            if text.startswith("B.Các"):
                section = "b"
                continue
            if ws[0][4] == "Tổng":  # dòng tổng: 6 số theo thứ tự (canh trái, không thẳng cột)
                totals[section] = [to_num(w[4]) for w in ws if is_amount(w[4])]
                continue
            name = " ".join(w[4] for w in ws if w[2] < 262)
            codes = [w[4] for w in ws if 262 <= w[0] < 380]
            if len(codes) == 2 and codes[1].isdigit():
                data[section].append({"ten_tk": name, "tk_nhnn": codes[0], "tk_fcc": codes[1],
                                      **dict(zip(["dk_no", "dk_co", "ps_no", "ps_co", "ck_no", "ck_co"], by_right_edge(ws, edges)))})
            elif name and not codes and data[section] and not any(is_amount(w[4]) for w in ws) and y > 150:
                data[section][-1]["ten_tk"] += " " + name  # tên tài khoản xuống dòng
    return data, totals


def nksc():
    edges = [420, 527, 635, 742, 845, 960]
    rows = []
    for page in fitz.open(SRC / "103699000.pdf"):
        for _, ws in lines(page):
            if re.fullmatch(r"\d{9}", ws[0][4]) and ws[0][0] < 100:
                name = " ".join(w[4] for w in ws[1:] if w[2] < 540)
                vals = by_right_edge([w for w in ws if w[0] > 500], edges)
                rows.append({"so_tk": ws[0][4], "ten_tk": name, **dict(zip(["dk_no", "dk_co", "ps_no", "ps_co", "ck_no", "ck_co"], vals))})
    return rows


# TK cấp 4 - 2 chi nhánh, nhập tay theo bố cục PDF (số liệu đã ẩn danh)
TK4 = [
    {"ma_cn": "001", "ten_cn": "Chi nhánh A", "loai_tien": "VND", "dk_no": 0, "dk_co": 0, "ps_no": 26000000000, "ps_co": 0, "ck_no": 26000000000, "ck_co": 0},
    {"ma_cn": "002", "ten_cn": "Chi nhánh B", "loai_tien": "VND", "dk_no": 0, "dk_co": 0, "ps_no": 12000000000, "ps_co": 0, "ck_no": 12000000000, "ck_co": 0},
]

# Nhật ký quỹ - loại tiền USD (PDF gốc lỗi font tên GDV -> nhập tay; tên, mã chứng từ đã ẩn danh)
NKQ_USD = [
    ("CT0000000001", "", 10000000.00, None, "Giao dịch viên 1", "gdv01.000000001"),
    ("CT0000000002", "", 10000.00, None, "Giao dịch viên 2", ""),
    ("CT0000000003", "", 1000.00, None, "Giao dịch viên 2", ""),
    ("CT0000000004", "MUA USD BAN VND", 100.00, None, "Giao dịch viên 3", ""),
    ("CT0000000005", "NỘP TIỀN MẶT", 2000000.00, None, "Giao dịch viên 3", ""),
    ("CT0000000006", "MUANT", 100.00, None, "Giao dịch viên 4", ""),
    ("CT0000000007", "BAN TM", None, 100.00, "Giao dịch viên 4", ""),
    ("CT0000000008", "DIEU QUY", 1000.00, None, "Giao dịch viên 5", ""),
    ("CT0000000009", "DIEU QUY", 2000.00, None, "Giao dịch viên 5", ""),
    ("CT0000000010", "NOP TK", 5000000.00, None, "Giao dịch viên 6", ""),
    ("CT0000000011", "", 1000.00, None, "Giao dịch viên 6", ""),
    ("CT0000000011", "", None, 1000.00, "", ""),
    ("CT0000000009", "DIEU QUY", None, 2000.00, "", ""),
    ("CT0000000002", "", None, 10000.00, "", ""),
    ("CT0000000008", "DIEU QUY", None, 1000.00, "", ""),
    ("CT0000000003", "", None, 1000.00, "", ""),
]
NKQ_USD_SUM = {"du_dau_ky": 0, "tong_thu": 17015200.00, "tong_chi": 15100.00, "du_cuoi_ky": 17000100.00}
