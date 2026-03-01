#!/usr/bin/env python3
"""HTML -> PDF renderer using headless Chrome/Chromium."""
import os
import subprocess
from pathlib import Path


CHROME_CANDIDATES = [
    os.environ.get("CHROME_BIN"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_chrome():
    for path in CHROME_CANDIDATES:
        if path and os.path.exists(path):
            return path
    return None


def html_to_pdf(html_path: str, pdf_path: str, chrome_path: str, timeout_s: int = 60):
    html_file = Path(html_path).resolve()
    pdf_file = Path(pdf_path).resolve()
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    if not html_file.exists():
        raise FileNotFoundError(f"HTML not found: {html_file}")
    if not chrome_path or not os.path.exists(chrome_path):
        raise FileNotFoundError(f"Chrome/Chromium not found: {chrome_path}")

    file_url = html_file.as_uri()
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--print-to-pdf={pdf_file}",
        "--virtual-time-budget=8000",
        file_url,
    ]
    subprocess.run(cmd, check=True, timeout=timeout_s)
    if not pdf_file.exists():
        raise RuntimeError(f"PDF render failed: {pdf_file}")
    return str(pdf_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render PDF from HTML using Chrome/Chromium")
    parser.add_argument("--input", required=True, help="HTML path")
    parser.add_argument("--output", required=True, help="PDF path")
    parser.add_argument("--chrome-path", default="", help="Chrome/Chromium binary path")
    args = parser.parse_args()

    chrome = args.chrome_path or find_chrome()
    if not chrome:
        raise SystemExit("Chrome/Chromium not found. Set --chrome-path or CHROME_BIN.")

    out = html_to_pdf(args.input, args.output, chrome)
    print(out)
