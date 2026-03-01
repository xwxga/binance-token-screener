#!/usr/bin/env python3
"""Daily runner for Binance Token Screener v4.0.
Finds the latest Excel in ./report and generates HTML+PDF into a timestamped output folder.
"""
import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path


DEFAULT_REPORT_DIR = Path("./report")
DEFAULT_OUTPUT_ROOT = Path("./v4_outputs")


def find_latest_excel(report_dir: Path) -> Path:
    candidates = list(report_dir.glob("*.xlsx"))
    if not candidates:
        raise FileNotFoundError(f"No .xlsx files found in {report_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(description="Daily runner for v4.0")
    parser.add_argument("--input", default="", help="Excel path (optional)")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Directory to search for Excel")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Output root directory")
    parser.add_argument("--top", type=int, default=8, help="Top N candidates")
    parser.add_argument("--sleep", type=float, default=0.15, help="Sleep between requests")
    parser.add_argument("--chrome-path", default="", help="Chrome/Chromium path for PDF")
    args = parser.parse_args()

    report_dir = Path(args.report_dir)
    output_root = Path(args.output_root)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_root / ts
    output_dir.mkdir(parents=True, exist_ok=True)

    excel_path = Path(args.input) if args.input else find_latest_excel(report_dir)
    report_basename = f"report_{ts}"

    cmd = [
        "python3",
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
