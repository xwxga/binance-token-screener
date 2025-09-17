# 币安代币筛选器部署指南
Binance Token Screener Deployment Guide

## 在新电脑上部署和配置步骤

### 1. 克隆代码仓库
```bash
git clone [your-repo-url]
cd binance_token_screener
```

### 2. 安装Python环境

#### 方法A：使用Anaconda（推荐）
```bash
# 下载并安装Anaconda: https://www.anaconda.com/download

# 创建虚拟环境
conda create -n crypto_project python=3.9
conda activate crypto_project

# 安装依赖
pip install -r requirements.txt
```

#### 方法B：使用系统Python
```bash
# 确保Python 3.9+已安装
python --version

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置飞书（Feishu/Lark）认证

创建 `feishu_config.json` 文件：
```json
{
  "app_id": "your_feishu_app_id",
  "app_secret": "your_feishu_app_secret"
}
```

**获取App ID和App Secret的步骤：**
1. 登录飞书开放平台：https://open.feishu.cn/
2. 创建或选择你的应用
3. 在应用详情页获取App ID和App Secret
4. 确保应用有以下权限：
   - `sheets:spreadsheet` - 创建和编辑表格
   - `drive:drive` - 访问云文档

### 4. 配置Telegram通知（可选但推荐）

运行设置向导获取chat_id：
```bash
python setup_telegram.py
```

**设置步骤：**
1. 运行上述命令
2. 打开Telegram，搜索 @binance_screener_bot
3. 发送 /start 或任意消息
4. 脚本会自动获取并保存你的chat_id

**配置文件 `telegram_config.json` 会自动生成：**
```json
{
  "bot_token": "8169474631:AAGJzotGIacWhBwi943mj_Wq1lus1hc3GpU",
  "chat_id": "自动获取的chat_id",
  "enabled": true
}
```

**Telegram通知功能：**
- 每次运行完成后自动发送报告
- 包含运行状态、耗时、错误信息
- 提供飞书表格链接
- 发送错误警报

### 5. 配置网络代理（如需要）

如果需要通过代理访问API，设置环境变量：
```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

或在代码中修改 `proxy_settings`（参考现有代码）。

### 6. 测试运行

首次手动运行测试：
```bash
# 使用conda环境
conda activate crypto_project
python binance_token_screener_v3.0.py

# 或使用系统Python
python binance_token_screener_v3.0.py
```

### 7. 配置自动定时运行

#### 启动后台调度器（每日7:45自动运行）
```bash
# 启动后台运行
./start_simple.sh background

# 查看状态
./start_simple.sh status

# 查看日志
./start_simple.sh logs

# 停止调度器
./start_simple.sh stop
```

#### 调度器特性：
- 自动在每天早上7:45运行
- 包含网络连接检查
- 自动日志轮转
- PID跟踪防止重复运行

### 8. 验证部署

检查以下文件是否存在：
- `feishu_config.json` - 飞书配置（必需）
- `telegram_config.json` - Telegram配置（可选）
- `scheduler.log` - 调度器日志
- `scheduler.pid` - 进程ID文件（运行时生成）
- `币安代币分析结果_YYYYMMDD/` - 输出目录（运行后生成）

### 9. 常见问题处理

#### 问题1：依赖包安装失败
```bash
# 更新pip
pip install --upgrade pip

# 逐个安装核心依赖
pip install pandas numpy requests
pip install openpyxl xlsxwriter
pip install schedule python-dateutil
```

#### 问题2：飞书认证失败
- 检查 `feishu_config.json` 中的app_id和app_secret
- 确保应用权限已正确配置
- 检查网络连接和代理设置

#### 问题3：调度器无法启动
```bash
# 检查Python路径
which python

# 修改start_simple.sh中的Python路径
nano start_simple.sh
# 将PYTHON_CMD改为你的Python路径
```

#### 问题4：币安API连接失败
- 检查网络连接
- 如需代理，确保代理设置正确
- 检查币安API是否在你的地区可访问

### 10. 输出文件结构

运行成功后会生成：
```
币安代币分析结果_YYYYMMDD/
├── Excel文件/
│   └── 币安代币分析_YYYYMMDD_HHMM.xlsx
├── 分析报告/
│   └── 分析报告_YYYYMMDD_HHMM.txt
└── 日志文件/
    └── 运行日志_YYYYMMDD_HHMM.log
```

飞书表格会自动创建在你的飞书云文档中。

### 11. 维护和监控

#### 查看日志
```bash
# 实时查看调度器日志
tail -f scheduler.log

# 查看最新运行日志
ls -la 币安代币分析结果_*/日志文件/
```

#### 手动运行（调试模式）
```bash
# 带详细输出的运行
python binance_token_screener_v3.0.py
```

#### 清理旧数据（可选）
```bash
# 删除30天前的结果
find . -name "币安代币分析结果_*" -type d -mtime +30 -exec rm -rf {} \;
```

---

## 快速部署清单

- [ ] 克隆代码库
- [ ] 安装Python 3.9+
- [ ] 创建虚拟环境
- [ ] 安装依赖包
- [ ] 创建 `feishu_config.json`
- [ ] 配置飞书应用权限
- [ ] 设置Telegram通知（可选）
- [ ] 测试手动运行
- [ ] 启动后台调度器
- [ ] 验证自动运行

完成以上步骤后，系统将每天自动运行并生成分析报告。

**支持联系**: 如遇到问题，请查看 `scheduler.log` 和运行日志获取详细错误信息。