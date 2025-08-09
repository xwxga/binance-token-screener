# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the Binance Token Screener repository.
本文件为Claude Code (claude.ai/code)提供币安代币筛选器代码库的使用指南。

## Project Overview / 项目概述

**Binance Token Screener v3.0** - A production-ready cryptocurrency analysis system that fetches real-time data from Binance APIs, performs multi-dimensional analysis, and generates comprehensive reports with Feishu (Lark) integration.

**币安代币筛选器 v3.0** - 生产就绪的加密货币分析系统，从币安API获取实时数据，执行多维度分析，并生成带有飞书表格集成的综合报告。

## Core Components / 核心组件

### Main Modules / 主要模块

1. **binance_token_screener_v3.0.py** - Main production screener with Feishu / 带飞书集成的主生产筛选器
   - Orchestrates the entire analysis pipeline / 协调整个分析管道
   - Manages user preferences and configuration / 管理用户偏好和配置
   - Handles Feishu authentication flow / 处理飞书认证流程
   - Creates output directories and files / 创建输出目录和文件
   - Integrates all analysis modules / 集成所有分析模块

2. **binance_token_screener_v2.0.py** - Legacy Google Sheets version / Google Sheets版本（旧版）

3. **feishu_manager.py** - Feishu API integration / 飞书API集成
   - Creates and manages Feishu spreadsheets / 创建和管理飞书表格
   - Handles data type conversion for API compatibility / 处理API兼容性的数据类型转换
   - Batch uploads data to multiple sheets / 批量上传数据到多个工作表
   - Manages sheet naming and properties / 管理工作表命名和属性

4. **coingecko_integration.py** - Real market cap data provider / 真实市值数据提供者
   - Fetches top market cap tokens from CoinGecko API / 从CoinGecko API获取市值前列代币
   - Implements caching (1-hour duration) to reduce API calls / 实现缓存(1小时)以减少API调用
   - Maps Binance symbols to CoinGecko IDs / 映射币安符号到CoinGecko ID
   - Provides real market cap, circulating supply, and FDV data / 提供真实市值、流通供应量和FDV数据

5. **data_supplement.py** - Missing token data supplementer / 缺失代币数据补充器
   - Fetches data for tokens not in the initial dataset / 获取初始数据集中缺失的代币数据
   - Retrieves spot/futures prices and volumes / 检索现货/期货价格和交易量
   - Calculates 14-day historical averages / 计算14天历史平均值
   - Gets funding rates for futures contracts / 获取期货合约的资金费率

6. **simple_scheduler.py** - Automated scheduling system / 自动调度系统
   - Runs daily at 7:45 AM / 每天早上7:45运行
   - Manages process lifecycle with PID tracking / 使用PID跟踪管理进程生命周期
   - Includes network connectivity checks / 包含网络连接检查
   - Comprehensive logging with rotation / 全面的日志记录和轮转

7. **oauth_setup_v1.0.py** - Legacy OAuth setup for Google Sheets / Google Sheets的OAuth设置（旧版）

## Quick Start / 快速开始

### 1. Setup Feishu Config / 设置飞书配置
```bash
# Create feishu_config.json with your App ID and App Secret
# 创建 feishu_config.json 并填入您的 App ID 和 App Secret
echo '{
  "app_id": "your_app_id",
  "app_secret": "your_app_secret"
}' > feishu_config.json
```

### 2. Run the Screener / 运行筛选器
```bash
# Using conda environment (recommended) / 使用conda环境（推荐）
/Users/wenxiangxu/opt/anaconda3/envs/crypto_project/bin/python binance_token_screener_v3.0.py

# Using system Python / 使用系统Python
python binance_token_screener_v3.0.py

# For Google Sheets version / Google Sheets版本
python binance_token_screener_v2.0.py
```

### 3. Automated Daily Runs / 自动每日运行
```bash
# Start scheduler in background (no environment adjustment needed) / 在后台启动调度器（无需调整环境）
cd /Users/wenxiangxu/Desktop/alpha_team_code/binance_token_screener
./start_simple.sh background

# Other commands / 其他命令
./start_simple.sh status   # Check status / 检查状态
./start_simple.sh logs     # View logs / 查看日志
./start_simple.sh stop     # Stop scheduler / 停止调度器
```

## Analysis Dimensions - Algorithm Logic / 分析维度 - 算法逻辑

### 1. 原始数据 (Raw Data)
**Algorithm / 算法**: Direct data aggregation from multiple sources / 从多个数据源直接聚合数据
- **Data Sources / 数据源**: 
  - Binance Spot API: Top 80 tokens by 24h volume / 币安现货API：24小时交易量前80的代币
  - Binance Futures API: Top 80 futures contracts by 24h volume / 币安期货API：24小时交易量前80的期货合约
  - CoinGecko API: Real market cap data / CoinGecko API：真实市值数据
- **Processing / 处理流程**: 
  - Merge spot and futures data by base asset / 按基础资产合并现货和期货数据
  - Update with real market cap from CoinGecko / 使用CoinGecko的真实市值更新
  - Calculate 14-day averages for volumes / 计算交易量的14天平均值
  - Add funding rates and open interest / 添加资金费率和持仓量
- **Exclusions / 排除项**: Only stablecoins (USDC, FDUSD, USD1) / 仅稳定币

### 2. 交易量排行 (Volume Ranking)
**Algorithm / 算法**: Sort by total 24h trading volume (spot + futures) / 按24小时总交易量排序（现货+期货）
- **Data Source / 数据源**: Combined dataset from raw data / 来自原始数据的组合数据集
- **Processing / 处理流程**:
  - Calculate total_volume_24h = spot_volume_24h + futures_volume_24h / 计算总交易量
  - Sort descending by total_volume_24h / 按总交易量降序排序
  - Add volume_rank column / 添加交易量排名列
  - Include 7日涨跌 and 14日涨跌 columns / 包含7日涨跌和14日涨跌列
- **Exclusions / 排除项**: Only stablecoins / 仅稳定币

### 3. 市值排行 (Market Cap Ranking)
**Algorithm / 算法**: Sort by market capitalization / 按市值排序
- **Data Source / 数据源**: Tokens with market_cap > 0 / 市值大于0的代币
- **Processing / 处理流程**:
  - Filter tokens with valid market cap / 筛选有效市值的代币
  - Sort descending by market_cap / 按市值降序排序
  - Add mcap_rank column / 添加市值排名列
- **Exclusions / 排除项**: Stablecoins + Major coins (BTC, ETH, SOL, XRP, BNB) / 稳定币+主要币种

### 4. 涨跌排行 (Gainers/Losers)
**Algorithm / 算法**: Top 30 gainers and top 30 losers by 1-day return / 按1日收益率的前30涨幅和前30跌幅
- **Data Source / 数据源**: All tokens with price change data / 所有有价格变化数据的代币
- **Processing / 处理流程**:
  - Gainers: tokens with 1d_return > 0, sorted descending, top 30 / 涨幅榜：1日收益率>0的代币，降序排列，前30
  - Losers: tokens with 1d_return < 0, sorted ascending, top 30 / 跌幅榜：1日收益率<0的代币，升序排列，前30
  - Combine both lists with gain_loss_type indicator / 合并两个列表并标记涨跌类型
- **Exclusions / 排除项**: Stablecoins + Major coins / 稳定币+主要币种

### 5. 期货专注 (Futures Focus)
**Algorithm / 算法**: Comprehensive futures market analysis / 全面的期货市场分析
- **Data Source / 数据源**: All tokens with futures contracts / 所有有期货合约的代币
- **Processing / 处理流程**:
  - Filter tokens where has_futures = True / 筛选有期货合约的代币
  - Include open interest (OI) data in USD with M/B formatting / 包含以M/B格式显示的美元持仓量数据
  - Calculate 7-day average OI / 计算7天平均持仓量
  - Sort by futures_volume_24h descending / 按24小时期货交易量降序排序
  - Add futures_rank column / 添加期货排名列
- **Exclusions / 排除项**: Stablecoins + Major coins + Excluded tokens / 稳定币+主要币种+排除代币

### 6. 每日涨幅榜 (Daily Gainers History)
**Algorithm / 算法**: 14-day rolling history of daily top 20 gainers / 每日前20涨幅榜的14天滚动历史
- **Data Source / 数据源**: Daily top 20 tokens by 1d_return / 每日1日收益率前20的代币
- **Processing / 处理流程**:
  - Load historical data from daily_gainers_history.json / 从daily_gainers_history.json加载历史数据
  - Add today's top 20 gainers / 添加今日前20涨幅
  - Maintain 14-day window (remove oldest if > 14 days) / 保持14天窗口（超过14天则删除最旧的）
  - Format as 29 columns: Rank + 14 pairs of (Token, Date) / 格式化为29列：排名+14对(代币,日期)
- **Exclusions / 排除项**: Stablecoins + Major coins / 稳定币+主要币种

### 7. 低量高市值 (Low Volume High Market Cap)
**Algorithm / 算法**: Top 150 market cap tokens with lowest futures volume / 市值前150中期货交易量最低的代币
- **Data Sources / 数据源**:
  - CoinGecko: Top 150 tokens by market cap / CoinGecko：市值前150的代币
  - Binance Futures: Futures volume data / 币安期货：期货交易量数据
  - Data Supplement: Missing token data / 数据补充：缺失的代币数据
- **Processing / 处理流程**:
  1. Get top 150 market cap symbols from CoinGecko / 从CoinGecko获取市值前150的代币符号
  2. Find these tokens in our dataset / 在我们的数据集中查找这些代币
  3. Supplement missing tokens using DataSupplementer / 使用DataSupplementer补充缺失的代币
  4. Filter tokens with futures_volume_24h > 0 / 筛选期货交易量>0的代币
  5. Exclude major coins (BTC, ETH, BNB, SOL, XRP) / 排除主要币种
  6. Sort by futures_volume_24h ascending / 按期货交易量升序排序
  7. Select bottom 35 tokens / 选择最低的35个代币
- **Exclusions / 排除项**: Stablecoins + Major coins + Excluded tokens / 稳定币+主要币种+排除代币

### 8. 低市值高交易量 (Low Market Cap High Volume)
**Algorithm / 算法**: Lowest market cap to futures volume ratio / 最低的市值对期货交易量比率
- **Data Source / 数据源**: Tokens with futures trading / 有期货交易的代币
- **Processing / 处理流程**:
  - Filter tokens with futures_volume_24h > 0 / 筛选期货交易量>0的代币
  - Calculate ratio = market_cap / (futures_volume_24h / 1,000,000) / 计算比率
  - Sort by ratio ascending (lowest ratio = high volume relative to market cap) / 按比率升序排序（最低比率=相对市值的高交易量）
  - Select top 30 tokens / 选择前30个代币
- **Exclusions / 排除项**: Stablecoins only / 仅稳定币

## Data Processing Pipeline / 数据处理管道

1. **Data Collection / 数据收集**
   - Fetch spot market data (sortable by 24h volume) / 获取现货市场数据（可按24小时交易量排序）
   - Fetch futures market data (all USDT contracts) / 获取期货市场数据（所有USDT合约）
   - Get funding rates for each futures contract / 获取每个期货合约的资金费率
   - Fetch open interest data / 获取持仓量数据

2. **Data Enhancement / 数据增强**
   - Merge spot and futures data by base asset / 按基础资产合并现货和期货数据
   - Add real market cap from CoinGecko / 添加来自CoinGecko的真实市值
   - Calculate 14-day historical averages / 计算14天历史平均值
   - Calculate 7-day and 14-day price returns / 计算7天和14天价格收益率
   - Add data for missing high market cap tokens / 为缺失的高市值代币添加数据

3. **Anomaly Detection / 异常检测**
   - Futures volume growth vs 14d average (top 5) / 期货交易量增长对比14天平均值（前5）
   - Spot volume growth vs 14d average (top 5) / 现货交易量增长对比14天平均值（前5）
   - 1-day return extremes (top/bottom 5) / 1日收益率极值（前5/后5）
   - 14-day return extremes (top/bottom 5) / 14日收益率极值（前5/后5）
   - Volume vs market cap outliers / 交易量对市值异常值
   - Funding rate anomalies / 资金费率异常
   - Open interest anomalies / 持仓量异常

4. **Output Generation / 输出生成**
   - Create Excel workbook with all 8 worksheets / 创建包含所有8个工作表的Excel工作簿
   - Format data with appropriate units (M/B for large numbers) / 使用适当单位格式化数据（大数字用M/B）
   - Apply conditional formatting for anomalies / 对异常值应用条件格式
   - Upload to Google Sheets with same structure / 以相同结构上传到Google Sheets

## Configuration / 配置

### Environment / 环境
- **Conda Environment / Conda环境**: `/Users/wenxiangxu/opt/anaconda3/envs/crypto_project`
- **Python Version / Python版本**: 3.9+
- **Required Files / 必需文件**: 
  - `oauth_credentials.json` - OAuth client credentials (user must provide) / OAuth客户端凭据（用户必须提供）
  - `token.json` - OAuth access tokens (auto-generated) / OAuth访问令牌（自动生成）
  - `coingecko_market_data_cache.json` - Market cap cache (auto-generated) / 市值缓存（自动生成）
  - `daily_gainers_history.json` - Historical gainers data (auto-generated) / 历史涨幅数据（自动生成）

### Parameters / 参数
- **Spot Token Count / 现货代币数量**: Default 80 (user configurable) / 默认80（用户可配置）
- **Futures Token Count / 期货代币数量**: Default 80 (user configurable) / 默认80（用户可配置）
- **Top Market Cap Analysis / 顶级市值分析**: 150 tokens (for 低量高市值) / 150个代币（用于低量高市值）
- **Schedule Time / 调度时间**: Daily at 7:45 AM / 每天早上7:45
- **Cache Duration / 缓存时长**: 1 hour for CoinGecko data / CoinGecko数据1小时

### Exclusion Lists / 排除列表
- **Stablecoins / 稳定币**: USDC, FDUSD, USD1
- **Major Coins / 主要币种**: BTC, ETH, SOL, XRP, BNB (excluded from analysis tabs) / （从分析标签页中排除）
- **Excluded Tokens / 排除代币**: ALPACA, BNX, LINA, VIDT, AGIX, FTM

## Output Structure / 输出结构
```
币安代币分析结果_YYYYMMDD/
├── Excel文件/        # Excel workbooks with all analysis / 包含所有分析的Excel工作簿
├── CSV文件/          # Individual CSV files (if Excel fails) / 单独的CSV文件（Excel失败时）
├── 分析报告/         # Analysis reports / 分析报告
└── 日志文件/         # Logs and diagnostics / 日志和诊断信息
```

## Important Notes / 重要说明

- OAuth setup is required before first run / 首次运行前需要OAuth设置
- Requires stable internet connection / 需要稳定的网络连接
- Respects Binance API rate limits / 遵守币安API速率限制
- Creates new Google Sheet daily (no overwrites) / 每天创建新的Google Sheet（不覆盖）
- Chinese language interface and file names / 中文界面和文件名
- All monetary values in USD / 所有货币值均为美元
- Large numbers formatted as M (millions) or B (billions) / 大数字格式化为M（百万）或B（十亿）

---
**Version / 版本**: 3.0  
**Last Updated / 最后更新**: 2025-08-09