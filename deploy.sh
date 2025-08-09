#!/bin/bash

# Binance Token Screener 部署脚本
# Deploy script for Binance Token Screener
# 用于将本地代码部署到远程服务器 / Deploy local code to remote server

# 配置区域 / Configuration
REMOTE_USER="ubuntu"
REMOTE_HOST="18.143.63.196"
PEM_FILE="../crypto-personal.pem"
REMOTE_PATH="~/crypto_project/binance-token-screener"
LOCAL_PATH="/Users/wenxiangxu/Desktop/alpha_team_code/binance_token_screener"

# 颜色定义 / Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示使用说明 / Show usage
show_usage() {
    echo -e "${BLUE}Binance Token Screener 部署脚本${NC}"
    echo ""
    echo "用法 / Usage:"
    echo "  ./deploy.sh [命令]"
    echo ""
    echo "命令 / Commands:"
    echo "  deploy       - 完整部署（代码+配置） / Full deployment"
    echo "  sync         - 仅同步代码 / Sync code only"
    echo "  backup       - 备份远程配置 / Backup remote configs"
    echo "  logs         - 查看远程日志 / View remote logs"
    echo "  status       - 检查服务状态 / Check service status"
    echo "  setup        - 首次环境设置 / Initial setup"
    echo "  test         - 测试连接 / Test connection"
    echo ""
    exit 0
}

# SSH命令封装 / SSH command wrapper
ssh_cmd() {
    ssh -i "$PEM_FILE" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$@"
}

# SCP命令封装 / SCP command wrapper
scp_cmd() {
    scp -i "$PEM_FILE" -o StrictHostKeyChecking=no "$@"
}

# 测试连接 / Test connection
test_connection() {
    echo -e "${BLUE}测试服务器连接...${NC}"
    if ssh_cmd "echo '✅ 连接成功!'; uname -a"; then
        echo -e "${GREEN}服务器连接正常${NC}"
        return 0
    else
        echo -e "${RED}无法连接到服务器${NC}"
        return 1
    fi
}

# 部署代码 / Deploy code
deploy_code() {
    echo -e "${BLUE}开始部署到 $REMOTE_HOST${NC}"
    
    # 测试连接 / Test connection first
    if ! test_connection; then
        exit 1
    fi
    
    # 创建远程目录 / Create remote directory
    echo -e "${YELLOW}创建远程目录...${NC}"
    ssh_cmd "mkdir -p $REMOTE_PATH"
    
    # 同步Python文件 / Sync Python files
    echo -e "${YELLOW}同步Python文件...${NC}"
    for file in *.py; do
        if [[ ! "$file" =~ ^test_ ]] && [[ ! "$file" =~ ^debug_ ]]; then
            echo "  上传: $file"
            scp_cmd "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        fi
    done
    
    # 同步脚本文件 / Sync script files
    echo -e "${YELLOW}同步脚本文件...${NC}"
    if [ -f "start_simple.sh" ]; then
        scp_cmd "start_simple.sh" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    fi
    if [ -f "server_setup.sh" ]; then
        scp_cmd "server_setup.sh" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    fi
    
    # 设置执行权限 / Set execution permissions
    echo -e "${YELLOW}设置执行权限...${NC}"
    ssh_cmd "chmod +x $REMOTE_PATH/*.sh 2>/dev/null || true"
    
    # 同步requirements.txt / Sync requirements
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}同步依赖文件...${NC}"
        scp_cmd "requirements.txt" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    fi
    
    echo -e "${GREEN}部署完成！${NC}"
    echo ""
    echo "下一步："
    echo "1. SSH到服务器: ssh -i $PEM_FILE $REMOTE_USER@$REMOTE_HOST"
    echo "2. 进入目录: cd $REMOTE_PATH"
    echo "3. 激活环境: source venv/bin/activate"
    echo "4. 运行程序: python binance_token_screener_v2.0.py"
}

# 仅同步代码 / Sync code only
sync_code() {
    echo -e "${BLUE}同步代码到服务器...${NC}"
    
    if ! test_connection; then
        exit 1
    fi
    
    # 同步Python文件（排除测试文件） / Sync Python files
    for file in *.py; do
        if [[ ! "$file" =~ ^test_ ]] && [[ ! "$file" =~ ^debug_ ]]; then
            echo "同步: $file"
            scp_cmd "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        fi
    done
    
    echo -e "${GREEN}同步完成！${NC}"
}

# 备份远程配置 / Backup remote configs
backup_configs() {
    echo -e "${BLUE}备份远程配置文件...${NC}"
    
    BACKUP_DIR="./remote_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份JSON配置文件 / Backup JSON configs
    echo "备份到: $BACKUP_DIR"
    scp_cmd "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/*.json" "$BACKUP_DIR/" 2>/dev/null || {
        echo -e "${YELLOW}没有找到配置文件或备份失败${NC}"
    }
    
    if [ "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
        echo -e "${GREEN}配置已备份到: $BACKUP_DIR${NC}"
    else
        rmdir "$BACKUP_DIR"
        echo -e "${YELLOW}没有配置文件需要备份${NC}"
    fi
}

# 查看远程日志 / View remote logs
view_logs() {
    echo -e "${BLUE}查看远程日志...${NC}"
    
    ssh_cmd "
        cd $REMOTE_PATH 2>/dev/null || { echo '项目目录不存在'; exit 1; }
        
        if [ -f scheduler.log ]; then
            echo '=== 调度器日志 (最后30行) ==='
            tail -n 30 scheduler.log
        fi
        
        if [ -d logs ]; then
            echo ''
            echo '=== 最新运行日志 ==='
            ls -t logs/*.log 2>/dev/null | head -1 | xargs tail -n 30
        fi
        
        # 查看最新的输出目录
        latest_dir=\$(ls -d 币安代币分析结果* 2>/dev/null | tail -1)
        if [ -n \"\$latest_dir\" ]; then
            echo ''
            echo \"=== 最新运行: \$latest_dir ===\"
            ls -la \"\$latest_dir/Excel文件/\" 2>/dev/null | head -5
        fi
    "
}

# 检查服务状态 / Check service status
check_status() {
    echo -e "${BLUE}检查远程服务状态...${NC}"
    
    ssh_cmd "
        cd $REMOTE_PATH 2>/dev/null || { echo '❌ 项目目录不存在'; exit 1; }
        
        echo '📍 项目路径: $REMOTE_PATH'
        echo ''
        
        # 检查调度器进程 / Check scheduler process
        if [ -f simple_scheduler.pid ]; then
            PID=\$(cat simple_scheduler.pid)
            if ps -p \$PID > /dev/null 2>&1; then
                echo '✅ 调度器运行中 (PID: '\$PID')'
            else
                echo '❌ 调度器未运行（PID文件存在但进程已停止）'
            fi
        else
            echo '❌ 调度器未运行（无PID文件）'
        fi
        
        # 检查最后运行时间 / Check last run time
        latest_dir=\$(ls -d 币安代币分析结果* 2>/dev/null | tail -1)
        if [ -n \"\$latest_dir\" ]; then
            echo ''
            echo \"📅 最后运行: \$latest_dir\"
        fi
        
        # 检查配置文件 / Check config files
        echo ''
        echo '📋 配置文件状态:'
        [ -f oauth_credentials.json ] && echo '  ✅ oauth_credentials.json' || echo '  ❌ oauth_credentials.json (需要配置)'
        [ -f token.json ] && echo '  ✅ token.json (已认证)' || echo '  ⚠️  token.json (需要运行oauth_setup)'
        
        # 检查Python环境 / Check Python environment
        echo ''
        echo '🐍 Python环境:'
        if [ -d venv ]; then
            echo '  ✅ 虚拟环境已创建'
            source venv/bin/activate 2>/dev/null && {
                python --version 2>/dev/null | sed 's/^/  /'
            }
        else
            echo '  ❌ 虚拟环境未创建'
        fi
        
        # 检查依赖 / Check dependencies
        echo ''
        echo '📦 核心依赖状态:'
        source venv/bin/activate 2>/dev/null && {
            python -c 'import pandas; print(\"  ✅ pandas\")' 2>/dev/null || echo '  ❌ pandas'
            python -c 'import requests; print(\"  ✅ requests\")' 2>/dev/null || echo '  ❌ requests'
            python -c 'import openpyxl; print(\"  ✅ openpyxl\")' 2>/dev/null || echo '  ❌ openpyxl'
        }
    "
}

# 首次设置 / Initial setup
initial_setup() {
    echo -e "${BLUE}执行首次环境设置...${NC}"
    
    # 测试连接 / Test connection
    if ! test_connection; then
        exit 1
    fi
    
    # 创建目录 / Create directory
    echo -e "${YELLOW}创建项目目录...${NC}"
    ssh_cmd "mkdir -p ~/crypto_project"
    
    # 上传并执行设置脚本 / Upload and run setup script
    echo -e "${YELLOW}上传设置脚本...${NC}"
    if [ -f "server_setup.sh" ]; then
        scp_cmd "server_setup.sh" "$REMOTE_USER@$REMOTE_HOST:~/crypto_project/"
        
        echo -e "${YELLOW}执行设置脚本...${NC}"
        ssh_cmd "cd ~/crypto_project && chmod +x server_setup.sh && ./server_setup.sh"
    else
        echo -e "${RED}server_setup.sh 不存在！${NC}"
        exit 1
    fi
    
    # 部署代码 / Deploy code
    deploy_code
    
    # 上传OAuth凭据（如果存在） / Upload OAuth credentials if exists
    if [ -f "oauth_credentials.json" ]; then
        echo -e "${YELLOW}上传OAuth凭据...${NC}"
        scp_cmd "oauth_credentials.json" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
        echo -e "${GREEN}OAuth凭据已上传${NC}"
    else
        echo -e "${YELLOW}注意: oauth_credentials.json 不存在，请手动上传后运行oauth_setup${NC}"
    fi
    
    echo -e "${GREEN}初始设置完成！${NC}"
    echo ""
    echo "后续步骤："
    echo "1. SSH登录: ssh -i $PEM_FILE $REMOTE_USER@$REMOTE_HOST"
    echo "2. 进入目录: cd $REMOTE_PATH"
    echo "3. 激活环境: source venv/bin/activate"
    echo "4. 设置OAuth: python oauth_setup_v1.0.py"
    echo "5. 测试运行: python binance_token_screener_v2.0.py"
    echo "6. 启动调度: ./start_simple.sh background"
}

# 主程序 / Main program
case "${1:-help}" in
    deploy)
        deploy_code
        ;;
    sync)
        sync_code
        ;;
    backup)
        backup_configs
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    setup)
        initial_setup
        ;;
    test)
        test_connection
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        show_usage
        ;;
esac