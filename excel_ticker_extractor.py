#!/usr/bin/env python3
"""
Extract tickers from Excel using regex.
"""
import argparse
import json
import os
import re
from typing import List, Set

import pandas as pd

DEFAULT_IGNORE = {
    "ALPHA",
    "XAG",
    "XAU",
    "PEPE",
    "DOGE",
    "HYPE",
    "GWEI",
}

DEFAULT_REGEX = r"\b[A-Z0-9]{2,12}\b"


def normalize_token(token: str) -> str:
    return token.strip().upper()


def extract_from_text(text: str, pattern: re.Pattern, ignore: Set[str]) -> List[str]:
    tokens = []
    for m in pattern.findall(text):
        t = normalize_token(m)
        if t in ignore:
            continue
        tokens.append(t)
    return tokens


def extract_from_excel(path: str, regex: str, ignore: Set[str]) -> List[str]:
    pattern = re.compile(regex)
    tokens: List[str] = []

    xl = pd.ExcelFile(path)
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=None)
        for col in df.columns:
            series = df[col].astype(str)
            for cell in series:
                tokens.extend(extract_from_text(cell, pattern, ignore))

    # de-duplicate while preserving order
    seen = set()
    ordered = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def main():
    parser = argparse.ArgumentParser(description="Extract tickers from Excel using regex")
    parser.add_argument("--input", required=True, help="Path to Excel file")
    parser.add_argument("--regex", default=DEFAULT_REGEX, help="Regex for ticker extraction")
    parser.add_argument("--ignore", default="", help="Comma-separated tokens to ignore")
    parser.add_argument("--output", default="", help="Output JSON path")
    args = parser.parse_args()

    ignore = set(DEFAULT_IGNORE)
    if args.ignore:
        for t in args.ignore.split(","):
            t = normalize_token(t)
            if t:
                ignore.add(t)

    tickers = extract_from_excel(args.input, args.regex, ignore)
    out = {
        "input": os.path.abspath(args.input),
        "regex": args.regex,
        "ignore": sorted(ignore),
        "count": len(tickers),
        "tickers": tickers,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
