#!/usr/bin/env python3
"""
LLM analysis wrapper. Reads JSON input and prints structured JSON output.
This is a stub for wiring to OpenClaw/LLM gateway.
"""
import argparse
import json
import os
from typing import Any, Dict

DEFAULT_PROMPT = """
You are an analysis assistant. Given tickers, top gainers, and futures anomalies,
produce JSON with fields: date, top5_gainers, streak_anomalies, futures_focus_anomalies,
and a short_summary.
Return valid JSON only.
""".strip()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze(payload: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """
    Placeholder: replace with real LLM call. For now, echo a minimal structure.
    """
    return {
        "date": payload.get("date"),
        "top5_gainers": payload.get("top5_gainers", []),
        "streak_anomalies": payload.get("streak_anomalies", []),
        "futures_focus_anomalies": payload.get("futures_focus_anomalies", []),
        "short_summary": "LLM gateway not wired. Provide OpenClaw gateway config.",
        "_prompt_used": prompt[:200],
    }


def main():
    parser = argparse.ArgumentParser(description="LLM analysis stub")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--prompt", default="", help="Prompt override")
    parser.add_argument("--output", default="", help="Output JSON path")
    args = parser.parse_args()

    payload = load_json(args.input)
    prompt = args.prompt or os.getenv("LLM_PROMPT", DEFAULT_PROMPT)

    result = analyze(payload, prompt)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
