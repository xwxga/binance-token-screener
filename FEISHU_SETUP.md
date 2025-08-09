# Feishu (Lark) Setup Guide / 飞书设置指南

## Overview / 概述
This guide explains how to set up Feishu (Lark) integration for the Binance Token Screener v3.0.

本指南说明如何为币安代币筛选器 v3.0 设置飞书集成。

## Prerequisites / 前置要求

1. **Feishu Developer Account / 飞书开发者账号**
   - Register at https://open.feishu.cn / 在 https://open.feishu.cn 注册
   - Create a new app / 创建新应用

2. **Required Permissions / 所需权限**
   - `sheets:spreadsheet` - Create and manage spreadsheets / 创建和管理电子表格
   - `drive:drive` - Access drive files / 访问云文档文件

## Setup Steps / 设置步骤

### 1. Create Feishu App / 创建飞书应用

1. Login to Feishu Open Platform / 登录飞书开放平台
   ```
   https://open.feishu.cn
   ```

2. Create a new app / 创建新应用
   - Click "Create App" / 点击"创建应用"
   - Choose "Self-built App" / 选择"自建应用"
   - Enter app name: "Binance Token Screener" / 输入应用名称

3. Get App Credentials / 获取应用凭据
   - Navigate to "Credentials & Basic Info" / 导航到"凭证与基础信息"
   - Copy `App ID` and `App Secret` / 复制 App ID 和 App Secret

### 2. Configure Permissions / 配置权限

1. Go to "Permissions & Scopes" / 前往"权限管理"
2. Add the following permissions / 添加以下权限：
   - `sheets:spreadsheet` 
   - `drive:drive`
3. Apply for permissions / 申请权限
4. Publish the app (for internal use) / 发布应用（内部使用）

### 3. Configure Local Environment / 配置本地环境

1. Create configuration file / 创建配置文件:
```bash
cat > feishu_config.json << EOF
{
  "app_id": "your_app_id_here",
  "app_secret": "your_app_secret_here"
}
EOF
```

2. Verify configuration / 验证配置:
```bash
python -c "
import json
with open('feishu_config.json') as f:
    config = json.load(f)
    print('✅ Config loaded successfully')
    print(f'App ID: {config[\"app_id\"][:10]}...')
"
```

### 4. Test Connection / 测试连接

Run the test script / 运行测试脚本:
```bash
python -c "
from feishu_manager import FeishuManager
manager = FeishuManager()
if manager.authenticate():
    print('✅ Authentication successful / 认证成功')
else:
    print('❌ Authentication failed / 认证失败')
"
```

## Usage / 使用方法

### Run with Feishu Integration / 使用飞书集成运行

```bash
# Default run with 80/80 configuration
python binance_token_screener_v3.0.py

# Custom configuration
python binance_token_screener_v3.0.py --spot-count 100 --futures-count 100
```

### Automated Daily Runs / 自动每日运行

Update scheduler to use v3.0 / 更新调度器使用 v3.0:
```bash
# Edit simple_scheduler.py
# Change: self.main_script = "binance_token_screener_v2.0.py"
# To: self.main_script = "binance_token_screener_v3.0.py"

# Start scheduler
./start_simple.sh background
```

## Output / 输出

The screener will create a Feishu spreadsheet with the following sheets / 筛选器将创建包含以下工作表的飞书表格：

1. **原始数据** - Raw data from all sources
2. **交易量排行** - Volume ranking  
3. **市值排行** - Market cap ranking
4. **涨跌排行** - Gainers and losers
5. **期货专注** - Futures focus analysis
6. **每日涨幅榜** - Daily gainers history
7. **低量高市值** - Low volume high market cap
8. **低市值高交易量** - Low market cap high volume

## Troubleshooting / 故障排除

### Authentication Errors / 认证错误

If you encounter authentication errors / 如果遇到认证错误：

1. Verify App ID and App Secret are correct / 验证 App ID 和 App Secret 是否正确
2. Check app permissions are approved / 检查应用权限是否已批准
3. Ensure app is published / 确保应用已发布

### API Rate Limits / API 速率限制

Feishu API has rate limits / 飞书 API 有速率限制：
- 1000 requests per minute / 每分钟 1000 次请求
- The screener implements automatic retry with backoff / 筛选器实现了自动重试和退避

### Data Type Errors / 数据类型错误

The system automatically handles / 系统自动处理：
- Boolean to string conversion / 布尔值转字符串
- NaN/Inf to empty string / NaN/Inf 转空字符串
- Numpy types to Python native types / Numpy 类型转 Python 原生类型

## Migration from Google Sheets / 从 Google Sheets 迁移

If migrating from v2.0 (Google Sheets) to v3.0 (Feishu) / 如果从 v2.0 (Google Sheets) 迁移到 v3.0 (飞书)：

1. Data processing logic remains identical / 数据处理逻辑保持相同
2. Only the upload mechanism changes / 仅上传机制改变
3. Both versions can run in parallel / 两个版本可以并行运行

## Support / 支持

For issues or questions / 如有问题或疑问：
- Check logs in `币安代币分析结果_YYYYMMDD/日志文件/` 
- Review error messages in console output / 查看控制台输出中的错误消息
- Ensure network connectivity to Feishu API / 确保与飞书 API 的网络连接

---
**Version**: 1.0  
**Last Updated**: 2025-08-09