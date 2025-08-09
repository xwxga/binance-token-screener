#!/bin/bash

# Binance Token Screener 服务器环境配置脚本
# Server Setup Script for Binance Token Screener
# 用于在新服务器上配置运行环境 / Setup runtime environment on new server

# 颜色定义 / Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量 / Configuration variables
PROJECT_DIR="$HOME/crypto_project/binance-token-screener"
PYTHON_VERSION="3.9"
VENV_DIR="venv"

# 错误处理 / Error handling
set -e
trap 'echo -e "${RED}错误: 命令失败在第 $LINENO 行${NC}"' ERR

# 打印带颜色的消息 / Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# 检查是否为root用户 / Check if running as root
check_not_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_msg "$RED" "请不要使用root用户运行此脚本！"
        print_msg "$YELLOW" "请使用普通用户运行: ./server_setup.sh"
        exit 1
    fi
}

# 检测操作系统 / Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        print_msg "$RED" "无法检测操作系统"
        exit 1
    fi
    
    print_msg "$BLUE" "检测到系统: $OS $OS_VERSION"
}

# 更新系统包 / Update system packages
update_system() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "1. 更新系统包..."
    print_msg "$BLUE" "=========================================="
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt-get update
        sudo apt-get upgrade -y
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "amzn" ]; then
        sudo yum update -y
    else
        print_msg "$YELLOW" "未知的操作系统，跳过系统更新"
    fi
}

# 安装Python / Install Python
install_python() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "2. 安装Python ${PYTHON_VERSION}..."
    print_msg "$BLUE" "=========================================="
    
    # 检查Python是否已安装 / Check if Python is installed
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        print_msg "$GREEN" "Python ${PYTHON_VERSION} 已安装"
        python${PYTHON_VERSION} --version
    else
        if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
            # Ubuntu/Debian需要添加deadsnakes PPA来安装Python 3.9
            if [ "$OS" = "ubuntu" ]; then
                sudo apt-get install -y software-properties-common
                sudo add-apt-repository -y ppa:deadsnakes/ppa
                sudo apt-get update
            fi
            sudo apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip
        elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
            sudo yum install -y python39 python39-pip
        elif [ "$OS" = "amzn" ]; then
            # Amazon Linux 2
            sudo amazon-linux-extras install -y python3.8
            # 如果需要3.9，可能需要从源码编译
            print_msg "$YELLOW" "Amazon Linux可能需要从源码编译Python 3.9"
        fi
    fi
    
    # 验证安装 / Verify installation
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        print_msg "$GREEN" "✅ Python ${PYTHON_VERSION} 安装成功"
    elif command -v python3 &> /dev/null; then
        print_msg "$YELLOW" "使用系统默认Python3版本"
        PYTHON_VERSION="3"
    else
        print_msg "$RED" "Python安装失败！"
        exit 1
    fi
}

# 安装系统依赖 / Install system dependencies
install_dependencies() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "3. 安装系统依赖..."
    print_msg "$BLUE" "=========================================="
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt-get install -y git curl wget build-essential
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "amzn" ]; then
        sudo yum install -y git curl wget gcc gcc-c++ make
    fi
    
    print_msg "$GREEN" "✅ 系统依赖安装完成"
}

# 设置项目目录 / Setup project directory
setup_project_dir() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "4. 设置项目目录..."
    print_msg "$BLUE" "=========================================="
    
    # 创建项目目录 / Create project directory
    mkdir -p $(dirname "$PROJECT_DIR")
    
    # 如果目录已存在，询问是否覆盖 / Ask if directory exists
    if [ -d "$PROJECT_DIR" ]; then
        print_msg "$YELLOW" "项目目录已存在: $PROJECT_DIR"
        read -p "是否要重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
            mkdir -p "$PROJECT_DIR"
        fi
    else
        mkdir -p "$PROJECT_DIR"
    fi
    
    cd "$PROJECT_DIR"
    print_msg "$GREEN" "✅ 项目目录: $PROJECT_DIR"
}

# 创建Python虚拟环境 / Create Python virtual environment
setup_venv() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "5. 创建Python虚拟环境..."
    print_msg "$BLUE" "=========================================="
    
    cd "$PROJECT_DIR"
    
    # 删除旧的虚拟环境 / Remove old venv if exists
    if [ -d "$VENV_DIR" ]; then
        print_msg "$YELLOW" "删除旧的虚拟环境..."
        rm -rf "$VENV_DIR"
    fi
    
    # 创建新的虚拟环境 / Create new venv
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        python${PYTHON_VERSION} -m venv $VENV_DIR
    else
        python3 -m venv $VENV_DIR
    fi
    
    # 激活虚拟环境 / Activate venv
    source $VENV_DIR/bin/activate
    
    # 升级pip / Upgrade pip
    pip install --upgrade pip
    
    print_msg "$GREEN" "✅ 虚拟环境创建成功"
    print_msg "$YELLOW" "  激活命令: source $PROJECT_DIR/$VENV_DIR/bin/activate"
}

# 安装Python依赖 / Install Python dependencies
install_python_deps() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "6. 安装Python依赖..."
    print_msg "$BLUE" "=========================================="
    
    cd "$PROJECT_DIR"
    source $VENV_DIR/bin/activate
    
    # 创建requirements.txt如果不存在 / Create requirements.txt if not exists
    if [ ! -f "requirements.txt" ]; then
        print_msg "$YELLOW" "创建requirements.txt..."
        cat > requirements.txt << 'EOF'
pandas>=1.3.0
requests>=2.26.0
openpyxl>=3.0.9
google-auth>=2.0.0
google-auth-oauthlib>=0.4.6
google-auth-httplib2>=0.1.0
google-api-python-client>=2.50.0
pytz>=2021.3
EOF
    fi
    
    # 安装依赖 / Install dependencies
    pip install -r requirements.txt
    
    print_msg "$GREEN" "✅ Python依赖安装完成"
}

# 创建必要的目录 / Create necessary directories
create_directories() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "7. 创建必要的目录..."
    print_msg "$BLUE" "=========================================="
    
    cd "$PROJECT_DIR"
    
    mkdir -p logs
    mkdir -p report
    mkdir -p remote_backup
    
    print_msg "$GREEN" "✅ 目录创建完成"
}

# 设置定时任务 / Setup cron job
setup_cron() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "8. 配置定时任务（可选）..."
    print_msg "$BLUE" "=========================================="
    
    print_msg "$YELLOW" "是否要设置每日自动运行? (y/N): "
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 创建cron任务 / Create cron job
        CRON_CMD="45 7 * * * cd $PROJECT_DIR && ./start_simple.sh background >> logs/cron.log 2>&1"
        
        # 检查是否已存在 / Check if already exists
        if crontab -l 2>/dev/null | grep -q "binance-token-screener"; then
            print_msg "$YELLOW" "定时任务已存在"
        else
            (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
            print_msg "$GREEN" "✅ 定时任务已添加（每天7:45运行）"
        fi
        
        # 显示当前crontab / Show current crontab
        print_msg "$BLUE" "当前定时任务:"
        crontab -l | grep binance || true
    else
        print_msg "$YELLOW" "跳过定时任务设置"
    fi
}

# 创建systemd服务 / Create systemd service
setup_systemd() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "9. 创建systemd服务（可选）..."
    print_msg "$BLUE" "=========================================="
    
    print_msg "$YELLOW" "是否要创建systemd服务? (y/N): "
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 创建服务文件 / Create service file
        cat > /tmp/binance-screener.service << EOF
[Unit]
Description=Binance Token Screener Scheduler
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/$VENV_DIR/bin/python $PROJECT_DIR/simple_scheduler.py
Restart=on-failure
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/systemd.log
StandardError=append:$PROJECT_DIR/logs/systemd.error.log

[Install]
WantedBy=multi-user.target
EOF
        
        # 安装服务 / Install service
        sudo cp /tmp/binance-screener.service /etc/systemd/system/
        sudo systemctl daemon-reload
        
        print_msg "$GREEN" "✅ Systemd服务已创建"
        print_msg "$YELLOW" "  启动服务: sudo systemctl start binance-screener"
        print_msg "$YELLOW" "  开机自启: sudo systemctl enable binance-screener"
        print_msg "$YELLOW" "  查看状态: sudo systemctl status binance-screener"
    else
        print_msg "$YELLOW" "跳过systemd服务设置"
    fi
}

# 显示完成信息 / Show completion info
show_completion() {
    print_msg "$GREEN" "=========================================="
    print_msg "$GREEN" "🎉 服务器环境配置完成！"
    print_msg "$GREEN" "=========================================="
    echo ""
    print_msg "$BLUE" "项目信息:"
    print_msg "$YELLOW" "  项目目录: $PROJECT_DIR"
    print_msg "$YELLOW" "  Python版本: $(python3 --version)"
    print_msg "$YELLOW" "  虚拟环境: $PROJECT_DIR/$VENV_DIR"
    echo ""
    print_msg "$BLUE" "后续步骤:"
    print_msg "$YELLOW" "1. 上传代码文件到: $PROJECT_DIR"
    print_msg "$YELLOW" "2. 上传oauth_credentials.json配置文件"
    print_msg "$YELLOW" "3. 激活虚拟环境:"
    print_msg "$YELLOW" "   source $PROJECT_DIR/$VENV_DIR/bin/activate"
    print_msg "$YELLOW" "4. 运行OAuth设置:"
    print_msg "$YELLOW" "   python oauth_setup_v1.0.py"
    print_msg "$YELLOW" "5. 测试运行:"
    print_msg "$YELLOW" "   python binance_token_screener_v2.0.py"
    print_msg "$YELLOW" "6. 启动调度器:"
    print_msg "$YELLOW" "   ./start_simple.sh background"
    echo ""
    print_msg "$BLUE" "常用命令:"
    print_msg "$YELLOW" "  查看日志: tail -f $PROJECT_DIR/scheduler.log"
    print_msg "$YELLOW" "  查看状态: ./start_simple.sh status"
    print_msg "$YELLOW" "  停止服务: ./start_simple.sh stop"
}

# 主函数 / Main function
main() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "Binance Token Screener 服务器环境配置"
    print_msg "$BLUE" "=========================================="
    echo ""
    
    # 执行各步骤 / Execute steps
    check_not_root
    detect_os
    update_system
    install_python
    install_dependencies
    setup_project_dir
    setup_venv
    install_python_deps
    create_directories
    setup_cron
    setup_systemd
    show_completion
}

# 运行主函数 / Run main function
main "$@"