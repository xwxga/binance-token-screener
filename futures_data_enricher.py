#!/usr/bin/env python3
"""
Fetch futures data (klines, volume, OI, MACD, RSI) for candidate tickers.
Drops tickers without futures contracts.
"""
import argparse
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

BASE = "https://fapi.binance.com"
KLINE_LIMIT = 200
INTERVALS = ["1h", "4h", "1d"]


def ema(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    k = 2 / (period + 1)
    ema_vals = [values[0]]
    for v in values[1:]:
        ema_vals.append(v * k + ema_vals[-1] * (1 - k))
    return ema_vals


def macd_last(values: List[float]) -> Dict[str, Optional[float]]:
    if len(values) < 26:
        return {"macd": None, "signal": None, "hist": None}
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)
    macd_line = [a - b for a, b in zip(ema12[-len(ema26):], ema26)]
    signal_line = ema(macd_line, 9)
    hist = macd_line[-1] - signal_line[-1]
    return {
        "macd": macd_line[-1],
        "signal": signal_line[-1],
        "hist": hist,
    }


def macd_series(values: List[float], times: List[int]) -> Dict[str, List[Dict[str, float]]]:
    if len(values) < 26:
        return {"macd": [], "signal": [], "hist": []}
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)
    macd_line = [a - b for a, b in zip(ema12[-len(ema26):], ema26)]
    signal_line = ema(macd_line, 9)
    # align times to macd_line length
    t = times[-len(macd_line):]
    macd_out = [{"time": int(ts), "value": float(v)} for ts, v in zip(t, macd_line)]
    signal_out = [{"time": int(ts), "value": float(v)} for ts, v in zip(t[-len(signal_line):], signal_line)]
    # hist aligned to signal length
    hist_vals = [m - s for m, s in zip(macd_line[-len(signal_line):], signal_line)]
    hist_out = [{"time": int(ts), "value": float(v)} for ts, v in zip(t[-len(signal_line):], hist_vals)]
    return {"macd": macd_out, "signal": signal_out, "hist": hist_out}


def rsi_last(values: List[float], period: int = 14) -> Optional[float]:
    if len(values) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        diff = values[i] - values[i - 1]
        if diff >= 0:
            gains.append(diff)
        else:
            losses.append(-diff)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def rsi_series(values: List[float], times: List[int], period: int = 14) -> List[Dict[str, float]]:
    if len(values) < period + 1:
        return []
    out = []
    for i in range(period, len(values)):
        window = values[i - period : i + 1]
        r = rsi_last(window, period=period)
        if r is None:
            continue
        out.append({"time": int(times[i]), "value": float(r)})
    return out


def get_exchange_info() -> Dict[str, List[Dict]]:
    r = requests.get(f"{BASE}/fapi/v1/exchangeInfo", timeout=10)
    r.raise_for_status()
    data = r.json()
    symbols = data.get("symbols", [])
    by_base: Dict[str, List[Dict]] = {}
    for s in symbols:
        if s.get("contractType") != "PERPETUAL":
            continue
        if s.get("status") != "TRADING":
            continue
        if s.get("quoteAsset") != "USDT":
            continue
        base = s.get("baseAsset", "").upper()
        by_base.setdefault(base, []).append(s)
    return by_base


def select_symbol(base: str, by_base: Dict[str, List[Dict]]) -> Optional[str]:
    base = base.upper()
    if base not in by_base:
        return None
    candidates = by_base[base]
    exact = [c for c in candidates if c.get("symbol") == f"{base}USDT"]
    if exact:
        return exact[0].get("symbol")
    return candidates[0].get("symbol")


def get_24h_ticker_map() -> Dict[str, Dict]:
    r = requests.get(f"{BASE}/fapi/v1/ticker/24hr", timeout=10)
    r.raise_for_status()
    data = r.json()
    return {item.get("symbol"): item for item in data}


def get_klines(symbol: str, interval: str, limit: int = KLINE_LIMIT) -> List[List]:
    r = requests.get(
        f"{BASE}/fapi/v1/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_open_interest(symbol: str) -> Optional[float]:
    r = requests.get(
        f"{BASE}/fapi/v1/openInterest",
        params={"symbol": symbol},
        timeout=10,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    try:
        return float(data.get("openInterest", 0))
    except Exception:
        return None


def get_open_interest_hist(symbol: str, period: str = "4h", limit: int = 200) -> List[Dict]:
    r = requests.get(
        f"{BASE}/futures/data/openInterestHist",
        params={"symbol": symbol, "period": period, "limit": limit},
        timeout=10,
    )
    if r.status_code != 200:
        return []
    data = r.json()
    result = []
    for item in data:
        try:
            result.append({
                "time": int(item.get("timestamp", 0)),
                "open_interest": float(item.get("sumOpenInterest", 0)),
            })
        except Exception:
            continue
    return result


def build_interval_metrics(klines: List[List]) -> Dict[str, Optional[float]]:
    closes = [float(k[4]) for k in klines]
    quote_vols = [float(k[7]) for k in klines]
    if len(closes) < 2:
        return {
            "close": None,
            "prev_close": None,
            "return_pct": None,
            "quote_volume": None,
            "macd": None,
            "signal": None,
            "hist": None,
            "rsi": None,
        }
    last = closes[-1]
    prev = closes[-2]
    ret = ((last / prev) - 1) * 100 if prev else None
    macd_vals = macd_last(closes)
    rsi_val = rsi_last(closes)
    return {
        "close": last,
        "prev_close": prev,
        "return_pct": ret,
        "quote_volume": quote_vols[-1] if quote_vols else None,
        "macd": macd_vals["macd"],
        "signal": macd_vals["signal"],
        "hist": macd_vals["hist"],
        "rsi": rsi_val,
    }


def klines_to_candles(klines: List[List]) -> List[Dict]:
    candles = []
    for k in klines:
        candles.append({
            "time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "quote_volume": float(k[7]),
        })
    return candles


def enrich_candidates(candidates: List[str], sleep_s: float = 0.15) -> Dict:
    by_base = get_exchange_info()
    ticker_map = get_24h_ticker_map()

    enriched = []
    dropped = []

    for base in candidates:
        symbol = select_symbol(base, by_base)
        if not symbol:
            dropped.append({"symbol": base, "reason": "no_futures_contract"})
            continue

        item = {
            "base_asset": base,
            "symbol": symbol,
            "intervals": {},
            "indicators_4h": {},
            "open_interest": None,
            "open_interest_4h": [],
            "open_interest_usdt_4h": [],
            "ticker_24h": {},
            "candles_4h": [],
        }

        t24 = ticker_map.get(symbol, {})
        item["ticker_24h"] = {
            "lastPrice": t24.get("lastPrice"),
            "quoteVolume": t24.get("quoteVolume"),
            "volume": t24.get("volume"),
            "priceChangePercent": t24.get("priceChangePercent"),
        }

        item["open_interest"] = get_open_interest(symbol)
        time.sleep(sleep_s)

        # klines for intervals
        for interval in INTERVALS:
            try:
                klines = get_klines(symbol, interval)
                item["intervals"][interval] = build_interval_metrics(klines)
                if interval == "4h":
                    item["candles_4h"] = klines_to_candles(klines)
                    times = [c["time"] for c in item["candles_4h"]]
                    closes = [c["close"] for c in item["candles_4h"]]
                    item["indicators_4h"] = macd_series(closes, times)
                    item["indicators_4h"]["rsi"] = rsi_series(closes, times)
            except Exception:
                item["intervals"][interval] = {
                    "close": None,
                    "prev_close": None,
                    "return_pct": None,
                    "quote_volume": None,
                    "macd": None,
                    "signal": None,
                    "hist": None,
                    "rsi": None,
                }
            time.sleep(sleep_s)

        # open interest history for 4h
        try:
            item["open_interest_4h"] = get_open_interest_hist(symbol, period="4h", limit=200)
            if item["open_interest_4h"] and item["candles_4h"]:
                price_map = {c["time"]: c["close"] for c in item["candles_4h"]}
                oi_usdt = []
                for o in item["open_interest_4h"]:
                    ts = o.get("time")
                    oi = o.get("open_interest")
                    if ts in price_map and oi is not None:
                        oi_usdt.append({"time": ts, "open_interest": float(oi) * float(price_map[ts])})
                item["open_interest_usdt_4h"] = oi_usdt
        except Exception:
            item["open_interest_4h"] = []
            item["open_interest_usdt_4h"] = []
        time.sleep(sleep_s)

        enriched.append(item)

    return {
        "date_generated": datetime.now().strftime("%Y-%m-%d"),
        "dropped": dropped,
        "enriched": enriched,
    }


def main():
    parser = argparse.ArgumentParser(description="Enrich candidates with futures data")
    parser.add_argument("--input", required=True, help="candidate selector output JSON")
    parser.add_argument("--output", default="", help="output JSON path")
    parser.add_argument("--sleep", type=float, default=0.15, help="sleep between requests")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    candidates = [c.get("symbol") for c in payload.get("candidates", [])]
    candidates = [c for c in candidates if c]

    out = enrich_candidates(candidates, sleep_s=args.sleep)
    out["input"] = payload

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
