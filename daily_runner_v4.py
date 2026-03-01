#!/usr/bin/env python3
"""Daily runner for Binance Token Screener v4.0.
Finds the latest Excel in ./report and generates HTML+PDF into a timestamped output folder.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime
DEFAULT_OUTPUT_ROOT = Path("./v4_outputs")
DEFAULT_V3_ROOT = Path(".")


def _latest_by_mtime(paths):
    return max(paths, key=lambda p: p.stat().st_mtime)


def find_latest_excel_from_v3(v3_root: Path) -> Path:
    # v3 outputs: 币安代币分析结果_YYYYMMDD/Excel文件/币安代币分析_YYYYMMDD_HHMM.xlsx
    folders = sorted(v3_root.glob("币安代币分析结果_*"))
    if not folders:
        raise FileNotFoundError(f"No v3 output folders found in {v3_root}")
    latest_folder = _latest_by_mtime(folders)
    excel_dir = latest_folder / "Excel文件"
    if not excel_dir.exists():
        raise FileNotFoundError(f"Excel folder not found: {excel_dir}")
    all_xlsx = list(excel_dir.glob("*.xlsx"))
    if not all_xlsx:
        raise FileNotFoundError(f"No .xlsx files found in {excel_dir}")
    # Prefer non-完整版 if present; otherwise take latest
    primary = [p for p in all_xlsx if "完整版" not in p.name]
    return _latest_by_mtime(primary) if primary else _latest_by_mtime(all_xlsx)


def main():
    parser = argparse.ArgumentParser(description="Daily runner for v4.0")
    parser.add_argument("--run-v3", action="store_true", help="Run v3.0 first to generate Excel + Feishu")
    parser.add_argument("--v3-python", default="", help="Python path for v3.0 (optional)")
    parser.add_argument("--spot-count", type=int, default=80, help="v3 spot count")
    parser.add_argument("--futures-count", type=int, default=80, help="v3 futures count")
    parser.add_argument("--top-gainers", type=int, default=5, help="v3 top gainers")
    parser.add_argument("--input", default="", help="Excel path (optional)")
    parser.add_argument("--v3-root", default=str(DEFAULT_V3_ROOT), help="Root directory for v3 outputs")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Output root directory")
    parser.add_argument("--top", type=int, default=8, help="Top N candidates")
    parser.add_argument("--sleep", type=float, default=0.15, help="Sleep between requests")
    parser.add_argument("--chrome-path", default="", help="Chrome/Chromium path for PDF")
    args = parser.parse_args()

    v3_root = Path(args.v3_root)
    output_root = Path(args.output_root)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_root / ts
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.run_v3:
        v3_python = args.v3_python or sys.executable
        v3_cmd = [
            v3_python,
            "binance_token_screener_v3.0.py",
            "--auto",
            "--spot-count",
            str(args.spot_count),
            "--futures-count",
            str(args.futures_count),
            "--top-gainers",
            str(args.top_gainers),
        ]
        env = os.environ.copy()
        # Ensure GCS is disabled for v3 runs
        env.pop("GCS_BUCKET", None)
        env.pop("GCS_HISTORY_BLOB", None)
        env.pop("GCS_OUTPUT_PREFIX", None)

        # Provide a stub google.cloud.storage module to avoid hard dependency
        with tempfile.TemporaryDirectory() as td:
            stub_root = Path(td)
            (stub_root / "google" / "cloud").mkdir(parents=True, exist_ok=True)
            (stub_root / "google" / "__init__.py").write_text("", encoding="utf-8")
            (stub_root / "google" / "cloud" / "__init__.py").write_text("", encoding="utf-8")
            (stub_root / "google" / "cloud" / "storage.py").write_text(
                "class Client:\\n"
                "    def __init__(self, *args, **kwargs):\\n"
                "        raise RuntimeError('GCS disabled in v4 runner')\\n",
                encoding="utf-8",
            )
            env["PYTHONPATH"] = f\"{stub_root}{os.pathsep}{env.get('PYTHONPATH','')}\"
            subprocess.run(v3_cmd, check=True, env=env)

    excel_path = Path(args.input) if args.input else find_latest_excel_from_v3(v3_root)
    report_basename = f"report_{ts}"

    cmd = [
        sys.executable,
        "binance_token_screener_v4.0.py",
        "--input",
        str(excel_path),
        "--output-dir",
        str(output_dir),
        "--top",
        str(args.top),
        "--sleep",
        str(args.sleep),
        "--report-basename",
        report_basename,
    ]
    if args.chrome_path:
        cmd.extend(["--chrome-path", args.chrome_path])

    subprocess.run(cmd, check=True)

    html_path = output_dir / f"{report_basename}.html"
    pdf_path = output_dir / f"{report_basename}.pdf"

    print(f"daily runner complete: {html_path} | {pdf_path}")


if __name__ == "__main__":
    main()
