"""Trích engine đang deploy từ các file Helm values -> package `customsso/` để kiểm tra template local.

Template phải được kiểm tra bằng ĐÚNG code trên Superset, nên luôn lấy từ YAML thay vì sửa tay bản copy.
Dùng: python3 sync_engine.py <thư mục đích> <values-report-builder.yaml> [values-dashboard-export.yaml]
Tạo:  <đích>/customsso/{__init__,rt_office,rt_format,rt_multi[,dr_errors,dr_docx]}.py
"""
import sys
from pathlib import Path

INDENT = "    "
REPORT_FILES = ("rt_office.py", "rt_format.py", "rt_multi.py")
DASHBOARD_FILES = ("dr_errors.py", "dr_docx.py")


def extract(yaml_text, name):
    """Lấy nội dung block scalar `  <name>: |` trong extraConfigs."""
    lines = yaml_text.splitlines()
    marker = f"  {name}: |"
    if marker not in lines:
        sys.exit(f"Không tìm thấy '{name}' trong YAML (phiên bản YAML quá cũ?).")
    body = []
    for line in lines[lines.index(marker) + 1:]:
        if line and not line.startswith(INDENT):
            break  # hết block: gặp key cùng cấp
        body.append(line[len(INDENT):])
    code = "\n".join(body).rstrip() + "\n"
    compile(code, name, "exec")  # fail sớm nếu cắt sai
    return code


def main(dest, report_yaml, dashboard_yaml=None):
    pkg = Path(dest) / "customsso"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    jobs = [(report_yaml, REPORT_FILES)] + ([(dashboard_yaml, DASHBOARD_FILES)] if dashboard_yaml else [])
    for yaml_path, names in jobs:
        text = Path(yaml_path).read_text(encoding="utf-8")
        for name in names:
            (pkg / name).write_text(extract(text, name), encoding="utf-8")
            print(f"OK {pkg / name}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
