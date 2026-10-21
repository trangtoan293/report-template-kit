"""Kiểm tra template .docx bằng ĐÚNG engine đang deploy (package customsso/ do sync_engine.py tạo).

Chế độ (giống Report Builder / Dashboard Export):
  per_row    1 dòng dataset = 1 báo cáo (mặc định)
  multi_row  group dòng theo --group-by, lặp các dòng bảng --repeat (tXrY[:cot=gia_tri])
  dashboard  template Dashboard Export: đúng 1 {#dashboard#} trong đoạn riêng; biến khác là text

Dùng:
  python3 check_template.py T.docx                                   # liệt kê biến + dòng lặp được (tXrY)
  python3 check_template.py T.docx --data row.json --pdf             # per_row, row.json = object
  python3 check_template.py T.docx --mode multi_row --data rows.json \
      --group-by ma_don_vi,tu_ngay --repeat t1r3:phan=A --repeat t2r3:phan=B \
      --mapping mapping.json --pdf                                   # rows.json = list object
  python3 check_template.py T.docx --mode dashboard [--data texts.json]
--mapping: {"bien": {"column": "cot", "aggregate": "sum", "number_format": "vi", "decimals": 0}, ...}
  biến không khai báo -> auto-map theo tên cột (như server); aggregate chỉ áp dụng multi_row.
Mã thoát != 0 khi có LỖI.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
try:
    from customsso import rt_multi, rt_office
except ImportError:
    sys.exit("Thiếu customsso/. Chạy: python3 sync_engine.py . <values-report-builder.yaml> [values-dashboard-export.yaml]")

GOOD_NAME = re.compile(r"[a-z][a-z0-9_]*")


def auto_mapping(variables, columns, overrides):
    """Mirror report_workflow.auto_mapping + ghi đè từ --mapping."""
    lookup = defaultdict(list)
    for c in columns:
        lookup[c.strip().casefold()].append(c)
    result = {}
    for v in variables:
        hits = lookup.get(v.strip().casefold(), [])
        column = v if v in columns else hits[0] if len(hits) == 1 else None
        result[v] = {"column": column} if column else {"blank": True}
        if v in overrides:
            result[v] = {"column": overrides[v]["column"]} if overrides[v].get("column") else result[v]
    return result


def parse_repeat(spec):
    ident, _, flt = spec.partition(":")
    column, _, value = flt.partition("=")
    return {"id": ident, "filter_column": column, "filter_value": value}


def lint_rows(variables, rows, mapping):
    errors, warns = [], [f"Tên biến lạ '{v}' - nên là snake_case ASCII (Word cắt vụn token?)"
                         for v in variables if not GOOD_NAME.fullmatch(v) and v != "dashboard"]
    blank = sorted(v for v, b in mapping.items() if "column" not in b)
    if blank:
        errors.append(f"{len(blank)} biến không có cột dataset: {', '.join(blank[:20])}")
    # Pattern list cũ (per_row, cột nhiều dòng): cùng tiền tố phải cùng số dòng
    lines = defaultdict(dict)
    for k, v in rows[0].items():
        if isinstance(v, str) and "\n" in v:
            lines[k.split("_")[0]][k] = v.count("\n") + 1
    errors += [f"Nhóm '{p}_*' lệch số dòng: {c}" for p, c in lines.items() if len(set(c.values())) > 1]
    return errors, warns


def run_report(office, args):
    raw = json.loads(Path(args.data).read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else [raw]
    if not rows or not all(isinstance(r, dict) for r in rows):
        sys.exit("--data phải là JSON object (per_row) hoặc list object (multi_row).")
    columns = list(dict.fromkeys(k for r in rows for k in r))
    overrides = json.loads(Path(args.mapping).read_text(encoding="utf-8")) if args.mapping else {}
    mapping = auto_mapping(office.variables, columns, overrides)
    errors, warns = lint_rows(office.variables, rows, mapping)
    payload = {"report_mode": args.mode, "mapping": overrides,
               "group_by": [c for c in (args.group_by or "").split(",") if c],
               "repeat_rows": [parse_repeat(s) for s in args.repeat]}
    try:
        definition = {"mapping": mapping, **rt_multi.normalize_multi(payload, set(columns), "docx", mapping)}
        if args.mode == "multi_row":
            rt_multi.validate_layout(office, definition["repeat_rows"])
        groups = rt_multi.group_indices(definition, rows)
        if args.mode == "per_row":
            groups = groups[:1]
        print(f"{len(rows)} dòng dữ liệu -> {len(groups)} báo cáo" + (" (per_row: chỉ điền dòng đầu)" if args.mode == "per_row" else ""))
        raws = [v for v, b in mapping.items() if "column" in b and b.get("number_format") == "raw"
                and isinstance(rows[0].get(b["column"]), (int, float)) and not isinstance(rows[0].get(b["column"]), bool)]
        if raws:
            warns.append(f"Biến số chưa cấu hình định dạng (in thô '1234567.0'): {', '.join(raws[:15])}"
                         " -> --mapping number_format vi/custom hoặc định dạng trong SQL")
        outputs = []
        if not errors:
            base = Path(args.out) if args.out else Path(args.template).with_name(Path(args.template).stem + "_filled.docx")
            for i, group in enumerate(groups, 1):
                out = base if len(groups) == 1 else base.with_name(f"{base.stem}_{i}{base.suffix}")
                out.write_bytes(rt_multi.merge_report(office, definition, [rows[j] for j in group], args.max_rows))
                outputs.append(out)
                print(f"  báo cáo {i}: {len(group)} dòng -> {out}")
    except rt_office.OfficeError as ex:
        errors.append(f"engine: {ex}")
        outputs = []
    return errors, warns, outputs


def run_dashboard(office, args):
    try:
        from customsso import dr_docx
        from customsso.dr_errors import ExportError
    except ImportError:
        sys.exit("Thiếu dr_docx. Chạy lại sync_engine.py kèm values-dashboard-export.yaml.")
    errors, warns = [], []
    try:
        dr_docx.slot(office)
    except ExportError as ex:
        errors.append(f"dashboard: {ex}")
    texts = json.loads(Path(args.data).read_text(encoding="utf-8")) if args.data else {}
    for v in office.variables:
        if v not in ("dashboard", "datetime") and v not in texts:
            warns.append(f"Biến '{v}': nhập text hoặc gán filter dashboard khi export (≤ 2.000 ký tự)")
    outputs = []
    if not errors and args.data:
        out = Path(args.out) if args.out else Path(args.template).with_name(Path(args.template).stem + "_filled.docx")
        out.write_bytes(office.merge({**texts, "dashboard": "[BẢNG DASHBOARD]", "datetime": "ngày 01 tháng 01 năm 2026"}))
        outputs.append(out)
    return errors, warns, outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("--mode", choices=("per_row", "multi_row", "dashboard"), default="per_row")
    ap.add_argument("--data")
    ap.add_argument("--mapping")
    ap.add_argument("--group-by")
    ap.add_argument("--repeat", action="append", default=[], help="tXrY hoặc tXrY:cot=gia_tri (lặp lại được)")
    ap.add_argument("--max-rows", type=int, default=2000, help="REPORT_BUILDER_MAX_ROWS_PER_REPORT")
    ap.add_argument("--out")
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()

    path = Path(a.template)
    try:
        office = rt_office.OfficeTemplate(path.read_bytes(), path.suffix.lstrip("."))
    except rt_office.OfficeError as ex:
        sys.exit(f"LỖI engine: {ex}")
    print(f"{path.name}: {len(office.variables)}/200 biến")
    print("  " + ", ".join(office.variables[:40]) + (" ..." if len(office.variables) > 40 else ""))
    for c in rt_multi.row_catalog(office):
        print(f"  dòng {c['id']}: {', '.join(c['variables'][:6])}{' ...' if len(c['variables']) > 6 else ''}"
              + (f"  [KHÔNG lặp được: {c['reason']}]" if c["reason"] else ""))

    errors, warns, outputs = [], [], []
    if a.mode == "dashboard":
        errors, warns, outputs = run_dashboard(office, a)
    elif a.data:
        errors, warns, outputs = run_report(office, a)
    elif a.mode == "multi_row":
        sys.exit("multi_row cần --data (list dòng).")

    if a.pdf and outputs and not errors:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outputs[0].parent), *map(str, outputs)],
                       check=True, capture_output=True)
        print("PDF ->", ", ".join(str(o.with_suffix(".pdf")) for o in outputs))
    for w in warns:
        print("CẢNH BÁO:", w)
    for e in errors:
        print("LỖI:", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
