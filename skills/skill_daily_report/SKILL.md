# skill_daily_report

## Purpose
Run the Binance Token Screener v4.0 pipeline daily and produce both HTML and PDF reports.

## Inputs
- Excel path (optional). If not provided, the latest `.xlsx` in `./report` is used.
- `top` (optional, default 8)
- `sleep` (optional, default 0.15)
- `chrome_path` (optional, for PDF rendering)

## Outputs
- `candidates.json`
- `enriched.json`
- `report_<timestamp>.html`
- `report_<timestamp>.pdf`

## Command
```bash
python3 daily_runner_v4.py \
  --report-dir ./report \
  --output-root ./v4_outputs \
  --top 8 \
  --sleep 0.15
```

## Notes
- PDF rendering requires Chrome/Chromium. Set `CHROME_BIN` or pass `--chrome-path`.
- Output is written into `./v4_outputs/<YYYYMMDD_HHMMSS>/`.
