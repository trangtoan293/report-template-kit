"""Dữ liệu mẫu dạng DÀI cho BM04M (multi_row) + cấu hình mapping định dạng/aggregate.

Đầu ra: _samples/BM04M_rows.json (list dòng như Superset trả), _samples/BM04M_mapping.json
Kiểm tra:
  python3 check_template.py ../BM04M_Bang_can_doi_tai_khoan_cap_III_multi.docx --mode multi_row \
    --data ../_samples/BM04M_rows.json --mapping ../_samples/BM04M_mapping.json \
    --group-by ma_don_vi,tu_ngay,den_ngay,loai_nguyen_te --repeat t1r3:phan=A --repeat t2r3:phan=B --pdf
"""
import json

import samples as S
from make_data import AMT6, SAMPLES

HEADER = {"ma_don_vi": "DV0311", "ten_ngan_hang": "NGÂN HÀNG MẪU", "ten_don_vi": "Chi nhánh A + PGD trực thuộc",
          "loai_nguyen_te": "Qui đổi", "tu_ngay": "01/07/2026", "den_ngay": "31/07/2026", "bieu_mau": "F01/TCTD",
          "can_cu_ban_hanh": "Ban hành theo Thông tư 27/TT-NHNN ngày 31/12/2021", "don_vi_tinh": "VN Đồng",
          "ngay_ky": "31", "thang_ky": "07", "nam_ky": "2026",
          "nguoi_lap": "Nguyễn Văn A", "nguoi_kiem_soat": "Trần Thị B", "lanh_dao": "Lê Văn C"}


def main():
    data, totals = S.cdtk3()
    # Tổng theo phần là cột của dataset (SQL: SUM(...) OVER (PARTITION BY khoá, phan) rồi pivot A/B),
    # vì aggregate của engine tính trên CẢ group, không lọc theo phần được.
    tong = {f"tong_{p}_{f}": v for p in ("a", "b") for f, v in zip(AMT6, totals[p])}
    rows = [{**HEADER, **tong, "phan": p.upper(), "stt": i, "sort_key": f"{p.upper()}{i:06d}",
             **{k: x[k] for k in ("ten_tk", "tk_nhnn", "tk_fcc", *AMT6)}}
            for p in ("a", "b") for i, x in enumerate(data[p], 1)]
    vi = {"number_format": "vi", "decimals": 0}
    mapping = {**{f: vi for f in AMT6}, **{k: {**vi, "aggregate": "first"} for k in tong}}
    SAMPLES.mkdir(exist_ok=True)
    (SAMPLES / "BM04M_rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (SAMPLES / "BM04M_mapping.json").write_text(json.dumps(mapping, indent=1), encoding="utf-8")
    print(f"BM04M: {len(rows)} dòng (A={len(data['a'])}, B={len(data['b'])})")


if __name__ == "__main__":
    main()
