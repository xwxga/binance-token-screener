#!/usr/bin/env python3
"""
Binance Token Screener v4.0
Pipeline:
1) Select candidates from Excel using weighted logic.
2) Enrich with Binance futures data (1h/4h/1d, OI, MACD, RSI).
3) Generate HTML report with 4h charts.
4) Optionally render PDF from the HTML report.
"""
import argparse
import json
import os
from datetime import datetime

import pandas as pd

from skill_candidate_selector import (
    compute_streaks,
    normalize_token,
    parse_history_pairs,
)
from futures_data_enricher import enrich_candidates
from report_generator_v4 import generate_report
from pdf_reporter import html_to_pdf, find_chrome

IGNORE_DEFAULT = {"ALPHA","XAG","XAU","PEPE","DOGE","HYPE","GWEI","OCEAN"}

DAY_WEIGHTS = {
    1: 0.7,
    2: 1.0,
    3: 0.7,
    4: 0.5,
    5: 0.4,
}

GAINERS_WEIGHT = 0.6
FUTURES_WEIGHT = 0.4


def build_futures_scores(fut: pd.DataFrame, ignore: set, max_rank: int = 15):
    scores = {}
    if "期货排名" not in fut.columns or "代币" not in fut.columns:
        return scores
    for _, row in fut.iterrows():
        rank = row.get("期货排名")
        if pd.isna(rank) or rank > max_rank:
            continue
        token = normalize_token(row.get("代币", ""))
        if not token or token in ignore:
            continue
        rank_weight = (max_rank + 1 - int(rank)) / max_rank
        scores[token] = max(scores.get(token, 0.0), rank_weight)
    return scores


def select_candidates_from_excel(path: str, top_n: int = 8, ignore=None):
    ignore = set(ignore or [])
    hist = pd.read_excel(path, sheet_name="每日涨幅榜", header=7)
    fut = pd.read_excel(path, sheet_name="期货专注", header=7)

    pairs = parse_history_pairs(hist)
    pairs = pairs[:5]

    gainers_scores = {}
    presence = {}
    top5_today = []

    for day_idx, (token_col, date_col) in enumerate(pairs, start=1):
        day_weight = DAY_WEIGHTS.get(day_idx, 0.0)
        for _, row in hist.iterrows():
            rank = row.get("排名")
            if pd.isna(rank) or rank > 10:
                continue
            token = normalize_token(row.get(token_col, ""))
            if not token or token in ignore:
                continue
            rank_weight = (10 + 1 - int(rank)) / 10
            gainers_scores[token] = gainers_scores.get(token, 0.0) + day_weight * rank_weight
            presence.setdefault(token, []).append(day_idx)
            if day_idx == 1 and int(rank) <= 5:
                if token not in top5_today:
                    top5_today.append(token)

    streaks = compute_streaks(presence)
    futures_scores = build_futures_scores(fut, ignore, max_rank=15)

    max_gainers = sum(DAY_WEIGHTS.values())
    max_futures = 1.0

    candidates = set(gainers_scores.keys()) | set(futures_scores.keys())
    results = []
    for token in candidates:
        gs = gainers_scores.get(token, 0.0) / max_gainers if max_gainers > 0 else 0.0
        fs = futures_scores.get(token, 0.0) / max_futures if max_futures > 0 else 0.0
        final = GAINERS_WEIGHT * gs + FUTURES_WEIGHT * fs
        results.append({
            "symbol": token,
            "score": round(final, 6),
            "gainers_score": round(gs, 6),
            "futures_score": round(fs, 6),
            "streak_days": int(streaks.get(token, 0)),
            "top5_today": token in top5_today,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "input": path,
        "date_generated": datetime.now().strftime("%Y-%m-%d"),
        "ignore": sorted(ignore),
        "top5_today": top5_today,
        "streaks_ge3": {k: v for k, v in streaks.items() if v >= 3},
        "candidates": results[:top_n],
    }


def main():
    parser = argparse.ArgumentParser(description="Binance Token Screener v4.0")
    parser.add_argument("--input", required=True, help="Excel path")
    parser.add_argument("--output-dir", default="./v4_outputs", help="Output directory")
    parser.add_argument("--top", type=int, default=8, help="Top N candidates")
    parser.add_argument("--sleep", type=float, default=0.15, help="Sleep between requests")
    parser.add_argument("--report-basename", default="report", help="Report base name (no extension)")
    pdf_group = parser.add_mutually_exclusive_group()
    pdf_group.add_argument("--pdf", action="store_true", help="Render PDF from HTML")
    pdf_group.add_argument("--no-pdf", action="store_true", help="Skip PDF render")
    parser.add_argument("--chrome-path", default="", help="Optional Chrome/Chromium binary path")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    selector_out = select_candidates_from_excel(args.input, top_n=args.top, ignore=IGNORE_DEFAULT)
    selector_path = os.path.join(args.output_dir, "candidates.json")
    with open(selector_path, "w", encoding="utf-8") as f:
        json.dump(selector_out, f, ensure_ascii=False, indent=2)

    enriched = enrich_candidates([c["symbol"] for c in selector_out["candidates"]], sleep_s=args.sleep)
    enriched["input"] = selector_out
    enriched_path = os.path.join(args.output_dir, "enriched.json")
    with open(enriched_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    report_base = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in args.report_basename)
    report_path = os.path.join(args.output_dir, f"{report_base}.html")
    generate_report(enriched, report_path)

    want_pdf = True if not args.no_pdf else False
    if args.pdf:
        want_pdf = True

    if want_pdf:
        pdf_path = os.path.join(args.output_dir, f"{report_base}.pdf")
        chrome = args.chrome_path or find_chrome()
        if not chrome:
            raise SystemExit("PDF render failed: Chrome/Chromium not found. Set --chrome-path or CHROME_BIN.")
        html_to_pdf(report_path, pdf_path, chrome_path=chrome)
        print(f"v4.0 complete: {report_path} | {pdf_path}")
    else:
        print(f"v4.0 complete: {report_path}")


if __name__ == "__main__":
    main()
