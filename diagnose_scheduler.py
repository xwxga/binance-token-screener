#!/usr/bin/env python3
"""
诊断调度器问题的脚本
"""

import os
import sys
import subprocess
import json

def check_paths():
    """检查路径配置"""
    print("=" * 50)
    print("1. 检查路径配置")
    print("=" * 50)
    
    # 检查当前目录
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    # 检查项目目录
    project_dirs = [
        "/Users/wenxiangxu/Desktop/alpha_team_code/binance_token_screener",
        os.path.expanduser("~/Desktop/alpha_team_code/binance_token_screener"),
        os.path.dirname(os.path.abspath(__file__))
    ]
    
    for project_dir in project_dirs:
        if os.path.exists(project_dir):
            print(f"✅ 项目目录存在: {project_dir}")
            # 列出目录内容
            files = os.listdir(project_dir)
            if "simple_scheduler.py" in files:
                print(f"  ✅ simple_scheduler.py 存在")
            else:
                print(f"  ❌ simple_scheduler.py 不存在")
            if "binance_token_screener_v3.0.py" in files:
                print(f"  ✅ binance_token_screener_v3.0.py 存在")
            else:
                print(f"  ❌ binance_token_screener_v3.0.py 不存在")
            break
        else:
            print(f"❌ 项目目录不存在: {project_dir}")
    
    print()

def check_python_env():
    """检查Python环境"""
    print("=" * 50)
    print("2. 检查Python环境")
    print("=" * 50)
    
    # 可能的Python路径
    python_paths = [
        "/Users/wenxiangxu/opt/anaconda3/envs/crypto_project/bin/python",
        os.path.expanduser("~/opt/anaconda3/envs/crypto_project/bin/python"),
        os.path.expanduser("~/anaconda3/envs/crypto_project/bin/python"),
        os.path.expanduser("~/miniconda3/envs/crypto_project/bin/python"),
        "/opt/anaconda3/envs/crypto_project/bin/python",
        "/usr/local/anaconda3/envs/crypto_project/bin/python",
        sys.executable  # 当前使用的Python
    ]
    
    found_python = None
    for python_path in python_paths:
        if os.path.exists(python_path):
            print(f"✅ Python存在: {python_path}")
            # 检查版本
            try:
                result = subprocess.run([python_path, "--version"], 
                                     capture_output=True, text=True)
                print(f"  版本: {result.stdout.strip()}")
                found_python = python_path
                
                # 检查必要的包
                packages = ["pandas", "requests", "schedule", "openpyxl"]
                for package in packages:
                    try:
                        result = subprocess.run(
                            [python_path, "-c", f"import {package}; print({package}.__version__)"],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            print(f"  ✅ {package}: {result.stdout.strip()}")
                        else:
                            print(f"  ❌ {package}: 未安装")
                    except:
                        print(f"  ❌ {package}: 检查失败")
                break
            except Exception as e:
                print(f"  ❌ 无法检查版本: {e}")
        else:
            print(f"❌ Python不存在: {python_path}")
    
    if not found_python:
        print("\n⚠️ 未找到配置的Python环境")
        print("当前系统Python:")
        print(f"  路径: {sys.executable}")
        print(f"  版本: {sys.version}")
    
    print()
    return found_python

def check_configs():
    """检查配置文件"""
    print("=" * 50)
    print("3. 检查配置文件")
    print("=" * 50)
    
    config_files = [
        "feishu_config.json",
        "telegram_config.json",
        "scheduler_config.json"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} 存在")
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # 不显示敏感信息
                    if "app_secret" in config:
                        config["app_secret"] = "***"
                    if "bot_token" in config:
                        config["bot_token"] = "***"
                    print(f"  内容: {json.dumps(config, indent=2)}")
            except Exception as e:
                print(f"  ❌ 读取失败: {e}")
        else:
            print(f"⚠️ {config_file} 不存在")
    
    print()

def test_direct_run(python_path=None):
    """测试直接运行调度器"""
    print("=" * 50)
    print("4. 测试直接运行调度器")
    print("=" * 50)
    
    if not python_path:
        python_path = sys.executable
    
    # 测试导入
    test_code = """
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    import simple_scheduler
    print("✅ 成功导入simple_scheduler")
    
    # 检查类
    scheduler = simple_scheduler.SimpleScheduler()
    print(f"✅ 创建调度器实例成功")
    print(f"  项目路径: {scheduler.project_path}")
    print(f"  Python路径: {scheduler.venv_path}")
    
    # 检查环境
    if scheduler.check_environment():
        print("✅ 环境检查通过")
    else:
        print("❌ 环境检查失败")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
"""
    
    try:
        result = subprocess.run(
            [python_path, "-c", test_code],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
    
    print()

def check_logs():
    """检查日志文件"""
    print("=" * 50)
    print("5. 检查日志文件")
    print("=" * 50)
    
    log_files = [
        "simple_scheduler.log",
        "simple_scheduler_output.log",
        "simple_scheduler_startup.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"✅ {log_file} 存在")
            # 显示最后几行
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"  最后5行:")
                        for line in lines[-5:]:
                            print(f"    {line.strip()}")
            except Exception as e:
                print(f"  ❌ 读取失败: {e}")
        else:
            print(f"⚠️ {log_file} 不存在")
    
    print()

def suggest_fixes():
    """建议修复方案"""
    print("=" * 50)
    print("6. 建议的修复步骤")
    print("=" * 50)
    
    print("""
1. 更新start_simple.sh中的路径:
   - PROJECT_DIR: 改为你的实际项目路径
   - VENV_PATH: 改为你的实际Python环境路径

2. 更新simple_scheduler.py中的路径:
   - self.project_path: 改为你的实际项目路径
   - self.venv_path: 改为你的实际Python环境路径

3. 确保Python环境有所需的包:
   pip install pandas requests schedule openpyxl xlsxwriter

4. 创建必要的配置文件:
   - feishu_config.json (飞书配置)
   - telegram_config.json (Telegram配置，可选)

5. 测试运行:
   python simple_scheduler.py (直接运行测试)
   ./start_simple.sh start (前台运行)
   ./start_simple.sh background (后台运行)
""")

def main():
    print("🔍 币安代币筛选器调度器诊断工具")
    print("=" * 50)
    
    # 执行各项检查
    check_paths()
    python_path = check_python_env()
    check_configs()
    test_direct_run(python_path)
    check_logs()
    suggest_fixes()
    
    print("\n诊断完成！请根据上述结果调整配置。")

if __name__ == "__main__":
    main()