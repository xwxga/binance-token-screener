# Changelog

All notable changes to the Binance Token Screener project will be documented in this file.

## [3.0.0] - 2025-08-09

### Added / 新增
- **Feishu (Lark) Integration** - Complete integration with Feishu spreadsheet API / 完整的飞书表格API集成
  - New `feishu_manager.py` module for API operations / 新的飞书API操作模块
  - Automatic spreadsheet creation with Chinese sheet names / 自动创建带中文工作表名的表格
  - Batch data upload with proper type conversion / 批量数据上传和类型转换
  - Sheet property management via PATCH API / 通过PATCH API管理工作表属性

### Changed / 变更
- **Primary Upload Platform** - Switched from Google Sheets to Feishu / 从Google Sheets切换到飞书
- **Configuration** - Now uses `feishu_config.json` instead of OAuth / 使用飞书配置文件代替OAuth
- **API Version** - Using Feishu Sheets API v2 for data operations / 使用飞书表格API v2进行数据操作
- **Documentation** - Updated all references from Google Sheets to Feishu / 更新所有Google Sheets引用为飞书

### Fixed / 修复
- Sheet naming issue - All sheets now display correct Chinese names / 工作表命名问题 - 所有工作表现在显示正确的中文名称
- Data type compatibility - Proper conversion of numpy types for API / 数据类型兼容性 - 正确转换numpy类型
- Boolean and NaN handling for Feishu API / 布尔值和NaN值的飞书API处理

### Technical Details / 技术细节
- Feishu API v2 endpoint: `/sheets/v2/spreadsheets/{token}/values_batch_update`
- Sheet renaming via PATCH: `/sheets/v3/spreadsheets/{token}/sheets/{sheet_id}`
- Data type conversions:
  - `bool` → `"TRUE"`/`"FALSE"` strings
  - `NaN`/`Inf` → empty string `""`
  - `numpy.int64`/`numpy.float64` → native Python `int`/`float`

## [2.0.0] - 2025-08-08

### Added / 新增
- **Google Sheets Integration** - OAuth-based automatic upload / 基于OAuth的自动上传
- **CoinGecko Integration** - Real market cap data with caching / 带缓存的真实市值数据
- **Data Supplement Module** - Fetch missing token data / 获取缺失代币数据
- **低量高市值 Analysis** - Top 150 market cap tokens with low futures volume / 市值前150低期货量分析
- **Automated Scheduler** - Daily runs at 7:45 AM / 每天7:45自动运行
- **Historical Data** - 14-day rolling history for daily gainers / 每日涨幅榜14天滚动历史

### Changed / 变更
- Expanded analysis from 50 to 80 tokens (configurable) / 分析范围从50扩展到80个代币（可配置）
- Enhanced data processing with 14-day averages / 增强数据处理包含14天平均值
- Improved error handling and logging / 改进错误处理和日志记录

### Fixed / 修复
- Market cap data accuracy using CoinGecko / 使用CoinGecko的市值数据准确性
- Futures volume calculations / 期货交易量计算
- Stablecoin exclusions across all tabs / 所有标签页的稳定币排除

## [1.0.0] - 2025-07-15

### Initial Release / 初始版本
- Basic Binance API integration / 基础币安API集成
- Spot and futures market data fetching / 现货和期货市场数据获取
- 8 analysis dimensions / 8个分析维度
- Excel and CSV export / Excel和CSV导出
- Basic anomaly detection / 基础异常检测

---

## Version History Summary / 版本历史摘要

- **v3.0** (2025-08-09): Feishu integration, maintaining feature parity with v2.0 / 飞书集成，保持与v2.0功能一致
- **v2.0** (2025-08-08): Google Sheets integration, production-ready release / Google Sheets集成，生产就绪版本
- **v1.0** (2025-07-15): Initial release with core functionality / 初始版本，核心功能

## Migration Notes / 迁移说明

### From v2.0 to v3.0
- Data processing logic remains identical / 数据处理逻辑保持相同
- Only upload mechanism changed (Google Sheets → Feishu) / 仅上传机制改变
- Both versions can coexist / 两个版本可共存
- Configuration: `oauth_credentials.json` → `feishu_config.json`

### From v1.0 to v2.0/v3.0
- Added real market cap data from CoinGecko / 添加CoinGecko真实市值数据
- Enhanced with 14-day historical calculations / 增强14天历史计算
- Automated scheduling support / 自动调度支持
- Cloud spreadsheet integration / 云表格集成