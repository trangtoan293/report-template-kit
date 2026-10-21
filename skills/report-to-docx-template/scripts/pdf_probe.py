"""Khảo sát PDF báo cáo mẫu: in từng dòng kèm toạ độ, gợi ý mép phải các cột số.

Kết quả dùng để: (1) đọc bố cục (header, cột, nhóm dòng) khi thiết kế template,
(2) lấy danh sách `edges` cho hàm trích số kiểu `by_right_edge` (xem examples/.../samples.py).
Dùng:
  python3 pdf_probe.py <file.pdf> [--pages 1-2] [--lines 80]
Cần PyMuPDF (pip install pymupdf).
"""
import argparse
import re
import unicodedata
from collections import Counter

import fitz

# Số kiểu VN "1.234.567", "(1.234)", "-1.234", "0"; số kiểu US "1,234.56" (báo cáo xuất từ T24)
AMOUNT = re.compile(r"^\(?-?(\d{1,3}([.,]\d{3})+([.,]\d+)?|\d+[.,]\d+|0)\)?$")


def lines(page, tol=2.5):
    # PDF ngân hàng hay dùng Unicode tổ hợp (NFD) -> chuẩn hoá NFC để so khớp chuỗi tiếng Việt
    words = sorted(((*w[:4], unicodedata.normalize("NFC", w[4])) for w in page.get_text("words")),
                   key=lambda w: (round(w[1]), w[0]))
    out = []
    for w in words:
        if out and abs(out[-1][0] - w[1]) < tol:
            out[-1][1].append(w)
        else:
            out.append([w[1], [w]])
    return [(y, sorted(ws, key=lambda w: w[0])) for y, ws in out]


def page_range(spec, n):
    if not spec:
        return range(n)
    a, _, b = spec.partition("-")
    return range(int(a) - 1, min(n, int(b or a)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="vd 1 hoặc 1-3 (mặc định: tất cả)")
    ap.add_argument("--lines", type=int, default=60, help="số dòng in ra mỗi trang (0 = không in)")
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    print(f"# {a.pdf}: {len(doc)} trang, khổ {doc[0].rect.width:.0f}x{doc[0].rect.height:.0f}pt "
          f"({'ngang' if doc[0].rect.width > doc[0].rect.height else 'dọc'})")
    edges = Counter()
    for p in page_range(a.pages, len(doc)):
        print(f"\n## Trang {p + 1}")
        for i, (y, ws) in enumerate(lines(doc[p])):
            for w in ws:
                if AMOUNT.match(w[4]):
                    edges[round(w[2] / 5) * 5] += 1  # gom mép phải theo bước 5pt
            if i < a.lines:
                print(f"y={y:6.1f} | " + "  ".join(f"{w[4]}@{w[0]:.0f}-{w[2]:.0f}" for w in ws))

    print("\n## Mép phải các cột số (x1 ~ số lần xuất hiện) -> ứng viên `edges`")
    for x, n in sorted(edges.items()):
        if n >= 3:
            print(f"  x1≈{x:5d}  {'#' * min(n, 60)} {n}")


if __name__ == "__main__":
    main()
