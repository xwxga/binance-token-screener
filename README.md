# Binance Token Screener v4.0 - Futures Report Edition

A production-ready cryptocurrency analysis system that fetches real-time data from Binance APIs, performs multi-dimensional analysis, and generates HTML + PDF reports for futures monitoring.

币安代币筛选器 - 生产就绪的加密货币分析系统，从币安API获取实时数据，执行多维度分析，并生成期货监控的 HTML + PDF 报告。

## Features / 功能特点

- **Real-time Data Fetching / 实时数据获取**: Fetches spot and futures market data from Binance APIs
- **Market Cap Integration / 市值集成**: Real market cap data from CoinGecko API with caching
- **Multi-dimensional Analysis / 多维度分析**: 8 different analysis perspectives including volume, market cap, gainers/losers
- **Automated Scheduling / 自动调度**: Daily runs via OpenClaw or local runner
- **HTML + PDF Reports / 报告输出**: 4h K线 + 成交量 + OI + MACD + RSI
- **Anomaly Detection / 异常检测**: Identifies unusual volume patterns and price movements

## Quick Start / 快速开始

### Prerequisites / 前置要求

- Python 3.9+
- Conda environment (recommended)
- Chrome/Chromium (for PDF rendering)
- Stable internet connection

### Installation / 安装

1. Clone the repository / 克隆仓库:
```bash
git clone https://github.com/yourusername/binance-token-screener.git
cd binance-token-screener
```

2. Create conda environment / 创建conda环境:
```bash
conda create -n crypto_project python=3.9
conda activate crypto_project
pip install -r requirements.txt
```

3. (Optional) Setup Feishu Config / 设置飞书配置（可选）:
`feishu_config.json` 不提交到 Git，需单独同步到网关主机。

### Usage / 使用方法

#### Manual Run / 手动运行
```bash
python daily_runner_v4.py \
  --report-dir ./report \
  --output-root ./v4_outputs \
  --top 8 \
  --sleep 0.15
```

#### Automated Daily Runs / 自动每日运行
Use OpenClaw scheduler (recommended) or a system cron.

#### GitHub Actions (Cloud) / GitHub Actions（云端）
Not recommended for v4.0. Use OpenClaw scheduler on gateway host.

## Security Notes / 安全说明

- **NEVER commit credentials**: `feishu_config.json`, `oauth_credentials.json` and `token.json` are in `.gitignore`
- **API Rate Limits**: The system respects Binance API rate limits
- **Proxy Support**: Configurable proxy settings for restricted networks

## License / 许可证

This project is for educational and research purposes only. Use at your own risk.

---

**Version**: 4.0  
**Last Updated**: 2026-03-02
