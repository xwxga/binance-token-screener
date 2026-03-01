#!/usr/bin/env python3
"""
Generate an HTML report with 4h candlestick, volume, OI, MACD, RSI
using TradingView Lightweight Charts.
"""
from datetime import datetime
import json

HTML_HEAD = """<!doctype html>
<html>
<head>
<meta charset=\"utf-8\" />
<title>Binance Futures Report</title>
<script src=\"https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js\"></script>
<script>
window.__lwQueue = [];
window.__lwRun = function(fn) {
  if (window.LightweightCharts) { fn(); return; }
  window.__lwQueue.push(fn);
};
(function() {
  function flush() {
    if (!window.LightweightCharts) return;
    while (window.__lwQueue.length) {
      const fn = window.__lwQueue.shift();
      try { fn(); } catch (e) { console.error(e); }
    }
  }
  function loadFallback() {
    if (window.LightweightCharts) { flush(); return; }
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/lightweight-charts/dist/lightweight-charts.standalone.production.js';
    s.onload = flush;
    document.head.appendChild(s);
  }
  setTimeout(loadFallback, 1500);
  setInterval(flush, 500);
})();
</script>
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
.section { margin-bottom: 40px; }
.hdr { margin-bottom: 8px; }
.small { color: #666; font-size: 12px; }
.chart { width: 100%; height: 320px; margin: 6px 0; }
.chart-sm { width: 100%; height: 200px; margin: 6px 0; }
.pane { border: 1px solid #eee; padding: 6px; }
.pane-grid { display: grid; grid-template-columns: 1fr; gap: 6px; }
</style>
</head>
<body>
<h1>Binance Futures Report (4h)</h1>
<p class=\"small\">Generated at __GENERATED__</p>
"""

HTML_FOOT = """</body></html>"""


def _fmt_series_time_ms_to_sec(candles):
    return [
        {
            "time": int(c["time"] / 1000),
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": c.get("quote_volume") or c.get("volume"),
        }
        for c in candles
    ]


def _fmt_line_series(time_val_pairs):
    return [
        {"time": int(t / 1000), "value": v}
        for t, v in time_val_pairs
        if t and v is not None
    ]


def generate_report(payload, output_path: str):
    parts = [HTML_HEAD.replace("__GENERATED__", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]

    for idx, item in enumerate(payload.get("enriched", []), start=1):
        base = item.get("base_asset")
        symbol = item.get("symbol")
        if not symbol:
            continue
        js_id = "".join(ch if ch.isalnum() else "_" for ch in symbol)
        if js_id and js_id[0].isdigit():
            js_id = "s_" + js_id
        js_id = f"{js_id}_{idx}"
        candles = item.get("candles_4h", [])
        oi_hist = item.get("open_interest_usdt_4h", []) or item.get("open_interest_4h", [])
        metrics_4h = item.get("intervals", {}).get("4h", {})
        indicators_4h = item.get("indicators_4h", {})

        if not candles:
            continue

        data = _fmt_series_time_ms_to_sec(candles)
        if data:
            max_time = max(d["time"] for d in data)
            min_time = max_time - (10 * 24 * 60 * 60)
            data = [d for d in data if d["time"] >= min_time]
        vol = [
            {
                "time": d["time"],
                "value": d.get("volume") or 0,
                "color": "#26a69a" if d["close"] >= d["open"] else "#ef5350",
            }
            for d in data
        ]

        oi_pairs = [(o.get("time", 0), o.get("open_interest")) for o in oi_hist]
        oi_series = _fmt_line_series(oi_pairs)
        if data:
            min_time = min(d["time"] for d in data)
            oi_series = [o for o in oi_series if o["time"] >= min_time]

        macd = metrics_4h.get("macd")
        signal = metrics_4h.get("signal")
        hist = metrics_4h.get("hist")
        rsi = metrics_4h.get("rsi")
        macd_series_raw = indicators_4h.get("macd", [])
        signal_series_raw = indicators_4h.get("signal", [])
        hist_series_raw = indicators_4h.get("hist", [])
        rsi_series_raw = indicators_4h.get("rsi", [])

        def _to_sec_series(series):
            out = []
            for p in series:
                try:
                    out.append({"time": int(p["time"] / 1000), "value": p["value"]})
                except Exception:
                    continue
            return out

        macd_series = _to_sec_series(macd_series_raw)
        signal_series = _to_sec_series(signal_series_raw)
        hist_series = _to_sec_series(hist_series_raw)
        rsi_series = _to_sec_series(rsi_series_raw)

        div_id = f"chart_{js_id}"
        parts.append("<div class=\"section\">")
        parts.append(f"<div class=\"hdr\"><strong>{base}</strong> ({symbol})</div>")
        parts.append(f"<div class=\"small\">4h MACD={macd} | RSI={rsi}</div>")

        parts.append("<div class=\"pane\">")
        parts.append("<div class=\"pane-grid\">")
        parts.append(f"<div id=\"{div_id}_price\" class=\"chart\"></div>")
        parts.append(f"<div id=\"{div_id}_voloi\" class=\"chart-sm\"></div>")
        parts.append(f"<div id=\"{div_id}_ind\" class=\"chart-sm\"></div>")
        parts.append("</div>")
        parts.append("</div>")
        parts.append("</div>")

        parts.append("<script>")
        parts.append("window.__lwRun(function(){")
        parts.append("(function(){")
        parts.append(f"var data_{js_id} = {json.dumps(data)};")
        parts.append(f"var vol_{js_id} = {json.dumps(vol)};")
        parts.append(f"var oi_{js_id} = {json.dumps(oi_series)};")
        parts.append(f"var macdData_{js_id} = {json.dumps(macd_series)};")
        parts.append(f"var signalData_{js_id} = {json.dumps(signal_series)};")
        parts.append(f"var histData_{js_id} = {json.dumps(hist_series)};")
        parts.append(f"var rsiData_{js_id} = {json.dumps(rsi_series)};")

        parts.append(
            f"var priceChart_{js_id} = LightweightCharts.createChart(document.getElementById('{div_id}_price'), {{ layout: {{ background: {{ color: '#ffffff' }}, textColor: '#333' }}, rightPriceScale: {{ visible: true }}, timeScale: {{ timeVisible: true }} }});"
        )
        parts.append(
            f"var voloiChart_{js_id} = LightweightCharts.createChart(document.getElementById('{div_id}_voloi'), {{ layout: {{ background: {{ color: '#ffffff' }}, textColor: '#333' }}, rightPriceScale: {{ visible: true }}, timeScale: {{ timeVisible: true }} }});"
        )
        parts.append(
            f"var indChart_{js_id} = LightweightCharts.createChart(document.getElementById('{div_id}_ind'), {{ layout: {{ background: {{ color: '#ffffff' }}, textColor: '#333' }}, rightPriceScale: {{ visible: true }}, timeScale: {{ timeVisible: true }} }});"
        )

        parts.append(
            f"var candleSeries_{js_id} = (priceChart_{js_id}.addCandlestickSeries ? priceChart_{js_id}.addCandlestickSeries() : priceChart_{js_id}.addSeries(LightweightCharts.CandlestickSeries));"
        )
        parts.append(f"candleSeries_{js_id}.setData(data_{js_id});")

        parts.append(
            f"var volSeries_{js_id} = (voloiChart_{js_id}.addHistogramSeries ? voloiChart_{js_id}.addHistogramSeries() : voloiChart_{js_id}.addSeries(LightweightCharts.HistogramSeries));"
        )
        parts.append(f"volSeries_{js_id}.setData(vol_{js_id});")

        parts.append(
            f"var oiSeries_{js_id} = (voloiChart_{js_id}.addLineSeries ? voloiChart_{js_id}.addLineSeries() : voloiChart_{js_id}.addSeries(LightweightCharts.LineSeries));"
        )
        parts.append(f"oiSeries_{js_id}.setData(oi_{js_id});")

        parts.append(
            f"var macdSeries_{js_id} = (indChart_{js_id}.addLineSeries ? indChart_{js_id}.addLineSeries() : indChart_{js_id}.addSeries(LightweightCharts.LineSeries));"
        )
        parts.append(
            f"var signalSeries_{js_id} = (indChart_{js_id}.addLineSeries ? indChart_{js_id}.addLineSeries() : indChart_{js_id}.addSeries(LightweightCharts.LineSeries));"
        )
        parts.append(
            f"var histSeries_{js_id} = (indChart_{js_id}.addHistogramSeries ? indChart_{js_id}.addHistogramSeries() : indChart_{js_id}.addSeries(LightweightCharts.HistogramSeries));"
        )
        parts.append(f"macdSeries_{js_id}.setData(macdData_{js_id});")
        parts.append(f"signalSeries_{js_id}.setData(signalData_{js_id});")
        parts.append(f"histSeries_{js_id}.setData(histData_{js_id});")

        parts.append(
            f"var rsiSeries_{js_id} = (indChart_{js_id}.addLineSeries ? indChart_{js_id}.addLineSeries() : indChart_{js_id}.addSeries(LightweightCharts.LineSeries));"
        )
        parts.append(f"rsiSeries_{js_id}.setData(rsiData_{js_id});")

        parts.append(f"var syncTimeRange_{js_id} = (range) => {{ if (range) {{ priceChart_{js_id}.timeScale().setVisibleRange(range); voloiChart_{js_id}.timeScale().setVisibleRange(range); indChart_{js_id}.timeScale().setVisibleRange(range); }} }};")
        parts.append(f"priceChart_{js_id}.timeScale().subscribeVisibleTimeRangeChange(syncTimeRange_{js_id});")
        parts.append(f"voloiChart_{js_id}.timeScale().subscribeVisibleTimeRangeChange(syncTimeRange_{js_id});")
        parts.append(f"indChart_{js_id}.timeScale().subscribeVisibleTimeRangeChange(syncTimeRange_{js_id});")

        parts.append("})();")
        parts.append("});")
        parts.append("</script>")

    parts.append(HTML_FOOT)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate HTML report from enriched data")
    parser.add_argument("--input", required=True, help="enriched JSON path")
    parser.add_argument("--output", required=True, help="output HTML path")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    generate_report(payload, args.output)
