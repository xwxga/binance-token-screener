# Binance Token Screener v3.0 - Feishu Edition

A production-ready cryptocurrency analysis system that fetches real-time data from Binance APIs, performs multi-dimensional analysis, and generates comprehensive reports with Feishu (Lark) integration.

币安代币筛选器 - 生产就绪的加密货币分析系统，从币安API获取实时数据，执行多维度分析，并生成带有飞书表格集成的综合报告。

## Features / 功能特点

- **Real-time Data Fetching / 实时数据获取**: Fetches spot and futures market data from Binance APIs
- **Market Cap Integration / 市值集成**: Real market cap data from CoinGecko API with caching
- **Multi-dimensional Analysis / 多维度分析**: 8 different analysis perspectives including volume, market cap, gainers/losers
- **Automated Scheduling / 自动调度**: Daily runs at 7:45 AM with simple scheduler
- **Feishu Integration / 飞书表格集成**: Automatic upload of analysis results to Feishu spreadsheets
- **Telegram Notifications / Telegram通知**: Automatic daily reports and error alerts via Telegram bot
- **Anomaly Detection / 异常检测**: Identifies unusual volume patterns and price movements

## Quick Start / 快速开始

### Prerequisites / 前置要求

- Python 3.9+
- Conda environment (recommended)
- Feishu App credentials (App ID and App Secret)
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

3. Setup Feishu Config / 设置飞书配置:
```bash
# Create feishu_config.json with your App ID and App Secret
echo '{
  "app_id": "your_app_id",
  "app_secret": "your_app_secret"
}' > feishu_config.json
```

4. Setup Telegram Notifications (Optional) / 设置Telegram通知（可选）:
```bash
# Run setup script to configure Telegram bot
python setup_telegram.py
# Or test with existing configuration
python telegram_notifier.py --test
```

### Usage / 使用方法

#### Manual Run / 手动运行
```bash
# For Feishu version (v3.0)
python binance_token_screener_v3.0.py

# For Google Sheets version (v2.0)
python binance_token_screener_v2.0.py
```

#### Automated Daily Runs / 自动每日运行
```bash
# Start scheduler in background
./start_simple.sh background

# Check status
./start_simple.sh status

# View logs
./start_simple.sh logs

# Stop scheduler
./start_simple.sh stop
```

## Security Notes / 安全说明

- **NEVER commit credentials**: `feishu_config.json`, `oauth_credentials.json` and `token.json` are in `.gitignore`
- **API Rate Limits**: The system respects Binance API rate limits
- **Proxy Support**: Configurable proxy settings for restricted networks

## License / 许可证

This project is for educational and research purposes only. Use at your own risk.

---

**Version**: 3.0  
**Last Updated**: 2025-08-09
