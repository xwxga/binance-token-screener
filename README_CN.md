# 币安代币筛选器 v3.0 - 飞书版

生产就绪的加密货币分析系统，从币安API获取实时数据，执行多维度分析，并生成带有飞书表格集成和Telegram通知的综合报告。

## 功能特点

- **实时数据获取**: 从币安API获取现货和期货市场数据
- **市值集成**: 通过CoinGecko API获取真实市值数据（带缓存）
- **多维度分析**: 8个不同的分析视角，包括交易量、市值、涨跌幅等
- **自动调度**: 每天早上7:45自动运行
- **飞书表格集成**: 自动上传分析结果到飞书表格
- **Telegram通知**: 通过Telegram机器人自动发送每日报告和错误警报
- **异常检测**: 识别异常交易量模式和价格变动
- **Cloud Run 定时**: 参见 `CLOUD_RUN.md`

## 快速开始

### 前置要求

- Python 3.9+
- Conda环境（推荐）
- 飞书应用凭据（App ID和App Secret）
- Telegram Bot Token（可选）
- 稳定的网络连接

### 安装步骤

#### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/binance-token-screener.git
cd binance-token-screener
```

#### 2. 创建conda环境
```bash
conda create -n crypto_project python=3.9
conda activate crypto_project
pip install -r requirements.txt
```

#### 3. 配置飞书
```bash
# 创建飞书配置文件
cat > feishu_config.json << EOF
{
  "app_id": "你的App_ID",
  "app_secret": "你的App_Secret"
}
EOF
```

详细设置请参考 [FEISHU_SETUP.md](FEISHU_SETUP.md)

#### 4. 配置Telegram通知（可选）
```bash
# 运行设置脚本配置Telegram机器人
python setup_telegram.py

# 测试配置
python telegram_notifier.py --test
```

## 使用方法

### 手动运行
```bash
# 飞书版本 (v3.0)
python binance_token_screener_v3.0.py

# 自定义配置
python binance_token_screener_v3.0.py --spot-count 100 --futures-count 100

# 自动模式（跳过所有用户输入）
python binance_token_screener_v3.0.py --auto
```

### 自动每日运行
```bash
# 在后台启动调度器
./start_simple.sh background

# 检查状态
./start_simple.sh status

# 查看日志
./start_simple.sh logs

# 停止调度器
./start_simple.sh stop
```

## 分析维度

系统提供8个专业的分析维度：

1. **原始数据** - 所有代币的完整数据集
2. **交易量排行** - 按24小时总交易量排序
3. **市值排行** - 按市值排序，排除稳定币和主要币种
4. **涨跌排行** - 前30涨幅和前30跌幅
5. **期货专注** - 期货市场深度分析
6. **每日涨幅榜** - 14天滚动历史记录
7. **低量高市值** - 市值前150中期货交易量最低的代币
8. **低市值高交易量** - 相对市值交易量最高的代币

## 输出结构
```
币安代币分析结果_YYYYMMDD/
├── Excel文件/        # 包含所有分析的Excel工作簿
├── CSV文件/          # 单独的CSV文件（备用）
├── 分析报告/         # 分析报告
└── 日志文件/         # 日志和诊断信息
```

## Telegram通知

系统会在每次运行后自动发送Telegram通知，包含：
- 运行状态（成功/失败/警告）
- 分析代币数量
- 飞书表格链接
- 错误和警告统计
- 详细日志文件附件

### 通知示例
```
📊 币安代币筛选器 - 每日报告
📅 2025-08-09 07:45:00

✅ 状态: 运行成功
⏱️ 耗时: 5分32秒
📈 分析代币: 80个现货 + 80个期货

📋 飞书表格:
https://feishu.cn/sheets/xxx

⚠️ 警告: 2个
❌ 错误: 0个

💾 详细日志已附上
```

## 版本历史

### v3.0.1 (2025-08-09)
- ✨ 新增Telegram机器人集成
- 📱 自动每日报告通知
- 🚨 关键故障错误警报
- 📎 日志文件附件支持

### v3.0.0 (2025-08-09)
- 🚀 完整的飞书表格API集成
- 📊 自动创建带中文工作表名的表格
- 🔄 批量数据上传和类型转换
- 🛠️ 通过PATCH API管理工作表属性

### v2.0.0 (2025-08-08)
- 📈 Google Sheets集成（已归档）
- 💰 CoinGecko真实市值数据
- 📊 14天历史数据分析
- ⏰ 自动调度系统

### v1.0.0 (2025-07-15)
- 🎯 初始版本发布
- 📡 基础币安API集成
- 📊 8个分析维度
- 💾 Excel和CSV导出

## 项目结构

```
binance_token_screener/
├── binance_token_screener_v3.0.py  # 主程序（飞书版）
├── feishu_manager.py                # 飞书API管理器
├── telegram_notifier.py            # Telegram通知模块
├── coingecko_integration.py        # CoinGecko市值数据
├── data_supplement.py               # 缺失数据补充
├── simple_scheduler.py              # 自动调度器
├── setup_telegram.py                # Telegram设置向导
├── feishu_config.json              # 飞书配置（需创建）
├── telegram_config.json            # Telegram配置（需创建）
└── archive/                         # 归档文件
    ├── binance_token_screener_v2.0.py  # Google Sheets版本
    └── oauth_setup_v1.0.py             # OAuth设置
```

## 配置说明

### 默认参数
- 现货代币数量: 80个
- 期货代币数量: 80个
- 调度时间: 每天7:45 AM
- 缓存时长: CoinGecko数据1小时

### 排除列表
- **稳定币**: USDC, FDUSD, USD1
- **主要币种**: BTC, ETH, SOL, XRP, BNB（从分析标签页中排除）
- **排除代币**: ALPACA, BNX, LINA, VIDT, AGIX, FTM

## 安全说明

- **永不提交凭据**: 所有配置文件都在`.gitignore`中
- `feishu_config.json` - 飞书凭据
- `telegram_config.json` - Telegram配置
- `oauth_credentials.json` - Google OAuth（已归档）
- `token.json` - 访问令牌

## 故障排除

### 飞书连接问题
- 验证App ID和App Secret是否正确
- 检查应用权限是否已批准
- 确保应用已发布

### Telegram通知问题
- 确保已向Bot发送 /start 消息
- 运行 `python setup_telegram.py` 重新配置
- 检查 `telegram_config.json` 中的chat_id

### API速率限制
- 币安API遵守速率限制
- 飞书API: 每分钟1000次请求
- 系统实现了自动重试和退避机制

## 技术细节

### 数据类型转换（飞书API兼容性）
- 布尔值 → "TRUE"/"FALSE" 字符串
- NaN/Inf → 空字符串 ""
- numpy.int64/float64 → Python原生 int/float

### API版本
- 飞书数据操作: v2 API
- 工作表重命名: v3 API with PATCH
- Telegram Bot API: 最新版本

## 贡献

欢迎提交问题和拉取请求。对于重大更改，请先开issue讨论。

## 许可证

本项目仅供教育和研究目的。使用风险自负。

---

**版本**: 3.0.1  
**最后更新**: 2025-08-09  
**作者**: 币安代币分析团队

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/yourusername/binance-token-screener/issues)
- Telegram: 通过配置的Bot接收通知
