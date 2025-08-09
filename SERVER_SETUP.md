# 服务器部署指南

## 快速开始

### 1. 克隆代码
```bash
# 克隆仓库
git clone https://github.com/xwxga/binance-token-screener.git
cd binance-token-screener

# 赋予执行权限
chmod +x server_init.sh
```

### 2. 运行初始化脚本
```bash
./server_init.sh
```

脚本会自动完成：
- ✅ 检查Python环境
- ✅ 创建虚拟环境
- ✅ 安装依赖包
- ✅ 配置飞书
- ✅ 配置Telegram（可选）
- ✅ 测试运行
- ✅ 设置定时任务
- ✅ 创建快捷命令

## 手动部署步骤

如果自动脚本失败，可以手动执行：

### 1. 环境准备
```bash
# 安装Python 3.9+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# 或者使用conda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
conda create -n crypto_project python=3.9
conda activate crypto_project
```

### 2. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install pandas requests openpyxl schedule numpy
```

### 3. 配置文件

#### 飞书配置
```bash
cat > feishu_config.json << EOF
{
  "app_id": "你的_app_id",
  "app_secret": "你的_app_secret"
}
EOF
```

#### Telegram配置（已配置好）
```bash
cat > telegram_config.json << EOF
{
  "bot_token": "8169474631:AAGJzotGIacWhBwi943mj_Wq1lus1hc3GpU",
  "chat_id": "1565225338",
  "enabled": true
}
EOF
```

### 4. 测试运行
```bash
# 激活虚拟环境
source venv/bin/activate

# 测试运行（小数据集）
python binance_token_screener_v3.0.py --auto --spot-count 20 --futures-count 20

# 正式运行
python binance_token_screener_v3.0.py --auto
```

## 设置自动运行

### 方法1：使用systemd（推荐）
```bash
# 创建服务文件
sudo nano /etc/systemd/system/binance-screener.service
```

内容：
```ini
[Unit]
Description=Binance Token Screener
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/path/to/binance-token-screener
ExecStart=/path/to/binance-token-screener/venv/bin/python /path/to/binance-token-screener/simple_scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable binance-screener
sudo systemctl start binance-screener
sudo systemctl status binance-screener
```

### 方法2：使用screen
```bash
# 安装screen
sudo apt install screen

# 创建新会话
screen -S binance-screener

# 在screen中运行
source venv/bin/activate
python simple_scheduler.py

# 分离会话：Ctrl+A, D
# 重新连接：screen -r binance-screener
```

### 方法3：使用nohup
```bash
# 后台运行
nohup venv/bin/python simple_scheduler.py > scheduler.log 2>&1 &

# 查看进程
ps aux | grep simple_scheduler

# 查看日志
tail -f scheduler.log
```

## 常用命令

### 运行命令
```bash
# 手动运行（交互式）
./run.sh

# 自动运行（跳过所有输入）
./auto_run.sh

# 自定义参数
./run.sh --spot-count 100 --futures-count 100

# 测试Telegram
./test_telegram.sh
```

### 日志查看
```bash
# 查看调度器日志
tail -f simple_scheduler.log

# 查看今日分析日志
ls -la 币安代币分析结果_$(date +%Y%m%d)/日志文件/

# 查看systemd日志
sudo journalctl -u binance-screener -f
```

### 进程管理
```bash
# 查看进程
ps aux | grep -E "simple_scheduler|binance_token"

# 停止进程
pkill -f simple_scheduler.py

# 重启systemd服务
sudo systemctl restart binance-screener
```

## 故障排除

### 1. Python版本问题
```bash
# 检查Python版本
python3 --version

# 如果版本低于3.9，安装新版本
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.9
```

### 2. 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 单独安装问题包
pip install pandas --no-cache-dir
pip install numpy --no-cache-dir
```

### 3. 权限问题
```bash
# 确保脚本有执行权限
chmod +x *.sh

# 确保目录有写入权限
chmod 755 .
```

### 4. 网络问题
```bash
# 测试API连接
curl https://api.binance.com/api/v3/ping

# 如需代理
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

### 5. Telegram通知失败
```bash
# 测试Bot连接
python -c "
import requests
bot_token = '8169474631:AAGJzotGIacWhBwi943mj_Wq1lus1hc3GpU'
url = f'https://api.telegram.org/bot{bot_token}/getMe'
print(requests.get(url).json())
"
```

## 监控建议

1. **设置日志轮转**
```bash
# 创建logrotate配置
sudo nano /etc/logrotate.d/binance-screener

# 内容
/path/to/binance-token-screener/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

2. **设置磁盘空间监控**
```bash
# 定期清理旧数据
find . -name "币安代币分析结果_*" -type d -mtime +30 -exec rm -rf {} \;
```

3. **设置健康检查**
```bash
# 添加到crontab
*/30 * * * * /path/to/check_health.sh
```

## 更新代码

```bash
# 停止服务
sudo systemctl stop binance-screener

# 更新代码
git pull origin main

# 重启服务
sudo systemctl start binance-screener
```

## 安全建议

1. **不要提交配置文件**
   - feishu_config.json
   - telegram_config.json
   - 这些文件已在.gitignore中

2. **使用环境变量**（可选）
```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
```

3. **限制文件权限**
```bash
chmod 600 *_config.json
```

---

## 快速测试

部署完成后，运行以下命令测试：

```bash
# 1. 测试Telegram通知
./test_telegram.sh

# 2. 小数据集测试
./run.sh --auto --spot-count 10 --futures-count 10

# 3. 查看输出
ls -la 币安代币分析结果_$(date +%Y%m%d)/
```

如果所有测试通过，系统就可以正常运行了！

每天7:45 AM会自动运行并发送Telegram通知到您的账号。