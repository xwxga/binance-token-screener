#!/bin/bash

# 简单的币安代币筛选器定时运行启动脚本
# 无需系统权限，只需要在后台持续运行

set -e

# 配置变量
PROJECT_DIR="/Users/wenxiangxu/Desktop/alpha_team_code/binance_token_screener"
VENV_PATH="/Users/wenxiangxu/opt/anaconda3/envs/crypto_project"
SCHEDULER_SCRIPT="simple_scheduler.py"
PID_FILE="$PROJECT_DIR/simple_scheduler.pid"
LOG_FILE="$PROJECT_DIR/simple_scheduler_startup.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# 检查环境
check_environment() {
    log "检查运行环境..."
    
    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "$VENV_PATH" ]; then
        error "虚拟环境不存在: $VENV_PATH"
        exit 1
    fi
    
    # 检查Python
    if [ ! -f "$VENV_PATH/bin/python" ]; then
        error "Python可执行文件不存在: $VENV_PATH/bin/python"
        exit 1
    fi
    
    # 检查调度器脚本
    if [ ! -f "$PROJECT_DIR/$SCHEDULER_SCRIPT" ]; then
        error "调度器脚本不存在: $PROJECT_DIR/$SCHEDULER_SCRIPT"
        exit 1
    fi
    
    success "环境检查通过"
}

# 检查是否已运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # 正在运行
        else
            # PID文件存在但进程不存在，删除PID文件
            rm -f "$PID_FILE"
            return 1  # 未运行
        fi
    else
        return 1  # 未运行
    fi
}

# 启动调度器（前台运行）
start_foreground() {
    log "启动币安代币筛选器定时调度器（前台运行）..."
    
    if check_running; then
        warning "调度器已在运行中 (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # 切换到项目目录
    cd "$PROJECT_DIR"
    
    # 直接运行调度器
    "$VENV_PATH/bin/python" "$SCHEDULER_SCRIPT"
}

# 启动调度器（后台运行）
start_background() {
    log "启动币安代币筛选器定时调度器（后台运行）..."
    
    if check_running; then
        warning "调度器已在运行中 (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # 切换到项目目录
    cd "$PROJECT_DIR"
    
    # 后台运行调度器
    nohup "$VENV_PATH/bin/python" "$SCHEDULER_SCRIPT" > simple_scheduler_output.log 2>&1 &
    
    # 保存PID
    echo $! > "$PID_FILE"
    
    # 等待一下确保启动成功
    sleep 3
    
    if check_running; then
        success "调度器启动成功 (PID: $(cat $PID_FILE))"
        log "日志文件: $PROJECT_DIR/simple_scheduler_output.log"
        log "PID文件: $PID_FILE"
        log "💡 调度器将在每天7:45自动执行"
        log "💡 查看状态: $0 status"
        log "💡 查看日志: $0 logs"
        log "💡 停止程序: $0 stop"
    else
        error "调度器启动失败"
        exit 1
    fi
}

# 停止调度器
stop_scheduler() {
    log "停止币安代币筛选器定时调度器..."
    
    if ! check_running; then
        warning "调度器未运行"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    # 发送TERM信号
    kill -TERM "$PID" 2>/dev/null || true
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # 如果还在运行，强制杀死
    if ps -p "$PID" > /dev/null 2>&1; then
        warning "进程未正常结束，强制终止..."
        kill -KILL "$PID" 2>/dev/null || true
        sleep 2
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    success "调度器已停止"
}

# 查看状态
show_status() {
    echo "🎯 币安代币筛选器简单定时调度器状态"
    echo "========================================"
    
    if check_running; then
        PID=$(cat "$PID_FILE")
        echo -e "状态: ${GREEN}运行中${NC}"
        echo "PID: $PID"
        
        # 显示进程信息
        if command -v ps > /dev/null; then
            echo "进程信息:"
            ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || echo "无法获取进程信息"
        fi
        
        # 显示最近的日志
        if [ -f "$PROJECT_DIR/simple_scheduler.log" ]; then
            echo ""
            echo "最近的日志 (最后10行):"
            tail -10 "$PROJECT_DIR/simple_scheduler.log" 2>/dev/null || echo "无法读取日志文件"
        fi
    else
        echo -e "状态: ${RED}未运行${NC}"
    fi
    
    echo ""
    echo "配置信息:"
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $VENV_PATH"
    echo "调度器脚本: $SCHEDULER_SCRIPT"
    echo "PID文件: $PID_FILE"
    echo "日志文件: $LOG_FILE"
    echo "执行时间: 每天 07:45"
}

# 查看日志
show_logs() {
    echo "🎯 币安代币筛选器调度器日志"
    echo "=========================="
    
    if [ -f "$PROJECT_DIR/simple_scheduler.log" ]; then
        echo "主日志文件 (最后50行):"
        tail -50 "$PROJECT_DIR/simple_scheduler.log"
    else
        warning "主日志文件不存在: $PROJECT_DIR/simple_scheduler.log"
    fi
    
    echo ""
    
    if [ -f "$PROJECT_DIR/simple_scheduler_output.log" ]; then
        echo "输出日志文件 (最后20行):"
        tail -20 "$PROJECT_DIR/simple_scheduler_output.log"
    else
        warning "输出日志文件不存在: $PROJECT_DIR/simple_scheduler_output.log"
    fi
}

# 显示帮助
show_help() {
    echo "🎯 币安代币筛选器简单定时调度器管理脚本"
    echo "=========================================="
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start       启动调度器（前台运行，推荐用于测试）"
    echo "  background  启动调度器（后台运行，推荐用于长期运行）"
    echo "  stop        停止调度器"
    echo "  restart     重启调度器"
    echo "  status      查看状态"
    echo "  logs        查看日志"
    echo "  help        显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 start          # 前台启动（可以看到实时输出）"
    echo "  $0 background     # 后台启动（推荐）"
    echo "  $0 status         # 查看运行状态"
    echo "  $0 logs           # 查看日志"
    echo ""
    echo "特点:"
    echo "  ✅ 无需系统权限"
    echo "  ✅ 每天7:45自动执行"
    echo "  ✅ 支持网络代理"
    echo "  ✅ 完整日志记录"
    echo "  ✅ 简单易用"
    echo ""
}

# 主函数
main() {
    # 创建日志文件
    touch "$LOG_FILE"
    
    case "${1:-help}" in
        start)
            check_environment
            start_foreground
            ;;
        background)
            check_environment
            start_background
            ;;
        stop)
            stop_scheduler
            ;;
        restart)
            check_environment
            stop_scheduler
            sleep 2
            start_background
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
