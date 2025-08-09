#!/bin/bash

# 服务器初始化脚本 - 币安代币筛选器 v3.0
# Server initialization script for Binance Token Screener v3.0

echo "=========================================="
echo "🚀 币安代币筛选器 - 服务器初始化"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python版本
check_python() {
    echo -e "${YELLOW}[1/8] 检查Python环境...${NC}"
    
    # 检查是否有Python 3.9+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ 未找到Python，请先安装Python 3.9+${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 找到Python: $PYTHON_CMD ($PYTHON_VERSION)${NC}"
}

# 创建虚拟环境
setup_venv() {
    echo -e "${YELLOW}[2/8] 创建虚拟环境...${NC}"
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
    else
        echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}[3/8] 安装依赖包...${NC}"
    
    # 升级pip
    pip install --upgrade pip > /dev/null 2>&1
    
    # 检查requirements.txt
    if [ ! -f "requirements.txt" ]; then
        echo -e "${YELLOW}⚠️ requirements.txt不存在，创建默认依赖...${NC}"
        cat > requirements.txt << EOF
pandas>=1.3.0
requests>=2.26.0
openpyxl>=3.0.0
schedule>=1.1.0
numpy>=1.21.0
EOF
    fi
    
    # 安装依赖
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 配置飞书
setup_feishu() {
    echo -e "${YELLOW}[4/8] 配置飞书...${NC}"
    
    if [ ! -f "feishu_config.json" ]; then
        echo -e "${YELLOW}请输入飞书配置信息：${NC}"
        read -p "App ID: " app_id
        read -p "App Secret: " app_secret
        
        cat > feishu_config.json << EOF
{
  "app_id": "$app_id",
  "app_secret": "$app_secret"
}
EOF
        echo -e "${GREEN}✅ 飞书配置已保存${NC}"
    else
        echo -e "${GREEN}✅ 飞书配置已存在${NC}"
    fi
}

# 配置Telegram
setup_telegram() {
    echo -e "${YELLOW}[5/8] 配置Telegram通知...${NC}"
    
    if [ ! -f "telegram_config.json" ]; then
        echo -e "${YELLOW}是否配置Telegram通知？(y/n): ${NC}"
        read -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 默认配置
            cat > telegram_config.json << EOF
{
  "bot_token": "8169474631:AAGJzotGIacWhBwi943mj_Wq1lus1hc3GpU",
  "chat_id": "1565225338",
  "enabled": true
}
EOF
            echo -e "${GREEN}✅ Telegram配置已创建（使用默认值）${NC}"
            echo -e "${YELLOW}   如需修改，请编辑 telegram_config.json${NC}"
        else
            cat > telegram_config.json << EOF
{
  "bot_token": "",
  "chat_id": "",
  "enabled": false
}
EOF
            echo -e "${YELLOW}⚠️ Telegram通知已禁用${NC}"
        fi
    else
        echo -e "${GREEN}✅ Telegram配置已存在${NC}"
    fi
}

# 测试运行
test_run() {
    echo -e "${YELLOW}[6/8] 测试运行...${NC}"
    echo -e "${YELLOW}是否进行测试运行？(y/n): ${NC}"
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}运行测试（使用默认参数）...${NC}"
        timeout 300 python binance_token_screener_v3.0.py --auto --spot-count 20 --futures-count 20
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 测试运行成功${NC}"
        else
            echo -e "${YELLOW}⚠️ 测试运行超时或失败${NC}"
        fi
    fi
}

# 设置定时任务
setup_scheduler() {
    echo -e "${YELLOW}[7/8] 配置定时任务...${NC}"
    echo -e "${YELLOW}是否设置每日自动运行？(y/n): ${NC}"
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 创建systemd服务文件
        sudo tee /etc/systemd/system/binance-screener.service > /dev/null << EOF
[Unit]
Description=Binance Token Screener Daily Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/simple_scheduler.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF
        
        # 启用并启动服务
        sudo systemctl daemon-reload
        sudo systemctl enable binance-screener.service
        sudo systemctl start binance-screener.service
        
        echo -e "${GREEN}✅ 定时任务已设置（每天7:45 AM运行）${NC}"
        echo -e "${YELLOW}   查看状态: sudo systemctl status binance-screener${NC}"
        echo -e "${YELLOW}   查看日志: sudo journalctl -u binance-screener -f${NC}"
    else
        echo -e "${YELLOW}⚠️ 跳过定时任务设置${NC}"
        echo -e "${YELLOW}   手动启动: ./start_simple.sh background${NC}"
    fi
}

# 创建快捷命令
create_shortcuts() {
    echo -e "${YELLOW}[8/8] 创建快捷命令...${NC}"
    
    # 创建run.sh
    cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python binance_token_screener_v3.0.py "$@"
EOF
    chmod +x run.sh
    
    # 创建auto_run.sh
    cat > auto_run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python binance_token_screener_v3.0.py --auto
EOF
    chmod +x auto_run.sh
    
    # 创建test_telegram.sh
    cat > test_telegram.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python telegram_notifier.py --test
EOF
    chmod +x test_telegram.sh
    
    echo -e "${GREEN}✅ 快捷命令已创建${NC}"
}

# 显示完成信息
show_completion() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}🎉 初始化完成！${NC}"
    echo "=========================================="
    echo ""
    echo "📚 快速使用指南："
    echo ""
    echo "1. 手动运行："
    echo "   ./run.sh                     # 交互式运行"
    echo "   ./auto_run.sh                # 自动运行（默认参数）"
    echo "   ./run.sh --spot-count 100    # 自定义参数"
    echo ""
    echo "2. Telegram测试："
    echo "   ./test_telegram.sh           # 测试通知"
    echo ""
    echo "3. 定时任务："
    if systemctl is-active --quiet binance-screener; then
        echo "   sudo systemctl status binance-screener  # 查看状态"
        echo "   sudo systemctl stop binance-screener    # 停止"
        echo "   sudo systemctl restart binance-screener # 重启"
        echo "   sudo journalctl -u binance-screener -f  # 查看日志"
    else
        echo "   ./start_simple.sh background  # 后台运行"
        echo "   ./start_simple.sh status      # 查看状态"
        echo "   ./start_simple.sh logs        # 查看日志"
        echo "   ./start_simple.sh stop        # 停止"
    fi
    echo ""
    echo "4. 配置文件："
    echo "   feishu_config.json           # 飞书配置"
    echo "   telegram_config.json         # Telegram配置"
    echo ""
    echo "📊 输出位置："
    echo "   币安代币分析结果_YYYYMMDD/   # 每日分析结果"
    echo ""
    echo "=========================================="
}

# 主流程
main() {
    # 检查是否在项目目录
    if [ ! -f "binance_token_screener_v3.0.py" ]; then
        echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
        echo -e "${YELLOW}   当前目录: $(pwd)${NC}"
        exit 1
    fi
    
    # 执行初始化步骤
    check_python
    setup_venv
    install_dependencies
    setup_feishu
    setup_telegram
    test_run
    setup_scheduler
    create_shortcuts
    show_completion
}

# 运行主流程
main