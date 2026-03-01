#!/usr/bin/env python3
"""
Select candidate tickers from Excel based on daily gainers history and futures focus.
Rules:
- Use daily gainers history (top10) with day weights (D1..D5) and rank weights.
- Use futures focus top15 with rank weights.
- Combine: gainers 0.6, futures 0.4 (both normalized).
- Ignore tickers in ignore list.
"""
import argparse
import json
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd

IGNORE_DEFAULT = {"ALPHA","XAG","XAU","PEPE","DOGE","HYPE","GWEI","OCEAN"}

DAY_WEIGHTS = {
    1: 0.7,  # D1
    2: 1.0,  # D2 (second date column)
    3: 0.7,  # D3
    4: 0.5,  # D4
    5: 0.4,  # D5
}

GAINERS_WEIGHT = 0.6
FUTURES_WEIGHT = 0.4


def normalize_token(t: str) -> str:
    return str(t).strip().upper()


def parse_history_pairs(df: pd.DataFrame) -> List[Tuple[str, str]]:
    pairs = []
    for col in df.columns:
        if str(col).startswith("代币"):
            suffix = str(col).replace("代币", "")
            date_col = "日期" + suffix
            if date_col in df.columns:
                pairs.append((col, date_col))
    return pairs


def build_gainers_scores(
    hist: pd.DataFrame,
    ignore: set,
    max_rank: int = 10,
    day_count: int = 5,
) -> Tuple[Dict[str, float], Dict[str, List[int]], List[str]]:
    pairs = parse_history_pairs(hist)
    pairs = pairs[:day_count]

    scores: Dict[str, float] = {}
    presence: Dict[str, List[int]] = {}

    top5_today: List[str] = []

    for day_idx, (token_col, date_col) in enumerate(pairs, start=1):
        day_weight = DAY_WEIGHTS.get(day_idx, 0.0)
        for _, row in hist.iterrows():
            rank = row.get("排名")
            if pd.isna(rank) or rank > max_rank:
                continue
            token = normalize_token(row.get(token_col, ""))
            if not token or token in ignore:
                continue

            rank_weight = (max_rank + 1 - int(rank)) / max_rank
            scores[token] = scores.get(token, 0.0) + day_weight * rank_weight
            presence.setdefault(token, []).append(day_idx)

            if day_idx == 1 and int(rank) <= 5:
                if token not in top5_today:
                    top5_today.append(token)

    return scores, presence, top5_today


def compute_streaks(presence: Dict[str, List[int]]) -> Dict[str, int]:
    streaks: Dict[str, int] = {}
    for token, days in presence.items():
        days_sorted = sorted(set(days))
        max_streak = 1
        cur = 1
        for i in range(1, len(days_sorted)):
            if days_sorted[i] == days_sorted[i-1] + 1:
                cur += 1
                max_streak = max(max_streak, cur)
            else:
                cur = 1
        if max_streak >= 3:
            streaks[token] = max_streak
    return streaks


def build_futures_scores(
    fut: pd.DataFrame,
    ignore: set,
    max_rank: int = 15,
) -> Dict[str, float]:
    scores: Dict[str, float] = {}
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


def main():
    parser = argparse.ArgumentParser(description="Candidate selector from Excel")
    parser.add_argument("--input", required=True, help="Excel path")
    parser.add_argument("--output", default="", help="Output JSON path")
    parser.add_argument("--top", type=int, default=8, help="Top N candidates")
    parser.add_argument("--ignore", default="", help="Comma-separated ignore list")
    args = parser.parse_args()

    ignore = set(IGNORE_DEFAULT)
    if args.ignore:
        for t in args.ignore.split(","):
            t = normalize_token(t)
            if t:
                ignore.add(t)

    hist = pd.read_excel(args.input, sheet_name="每日涨幅榜", header=7)
    fut = pd.read_excel(args.input, sheet_name="期货专注", header=7)

    gainers_scores, presence, top5_today = build_gainers_scores(hist, ignore)
    streaks = compute_streaks(presence)
    futures_scores = build_futures_scores(fut, ignore)

    max_gainers = sum(DAY_WEIGHTS.values())  # max when rank=1 for all days
    max_futures = 1.0

    # merge candidates
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
    top_results = results[: args.top]

    out = {
        "input": args.input,
        "date_generated": datetime.now().strftime("%Y-%m-%d"),
        "ignore": sorted(ignore),
        "top5_today": top5_today,
        "streaks_ge3": {k: v for k, v in streaks.items() if v >= 3},
        "candidates": top_results,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
