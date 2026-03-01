#!/usr/bin/env python3
"""
检查项目使用统计
包括 API 使用情况、文件系统、缓存状态等
"""

import os
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
import sys

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_file_size(filepath):
    """获取文件大小"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def check_oauth_token():
    """检查 OAuth token 状态"""
    print("\n" + "="*70)
    print("🔐 OAuth Token 状态")
    print("="*70)
    
    token_file = 'token.json'
    if not os.path.exists(token_file):
        print("❌ token.json 不存在")
        return
    
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        # 检查 scopes
        scopes = token_data.get('scopes', [])
        print(f"📋 权限范围 ({len(scopes)} 个):")
        required_scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        for scope in scopes:
            status = "✅" if scope in required_scopes else "ℹ️"
            print(f"   {status} {scope}")
        
        # 检查 refresh token
        has_refresh = 'refresh_token' in token_data and token_data['refresh_token']
        print(f"\n🔄 刷新令牌: {'✅ 已获取' if has_refresh else '❌ 未获取'}")
        
        # 检查过期时间
        if 'expiry' in token_data:
            try:
                expiry = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                now = datetime.now(expiry.tzinfo)
                if expiry > now:
                    remaining = expiry - now
                    print(f"⏰ 过期时间: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   剩余时间: {remaining}")
                else:
                    print(f"⚠️ 令牌已过期: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                print(f"⏰ 过期时间: {token_data.get('expiry', 'N/A')}")
        
        print(f"✅ Token 文件大小: {format_size(get_file_size(token_file))}")
        
    except Exception as e:
        print(f"❌ 读取 token.json 失败: {e}")

def check_feishu_config():
    """检查飞书配置"""
    print("\n" + "="*70)
    print("📱 飞书配置状态")
    print("="*70)
    
    config_file = 'feishu_config.json'
    if not os.path.exists(config_file):
        print("❌ feishu_config.json 不存在")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        app_id = config.get('app_id', '')
        app_secret = config.get('app_secret', '')
        
        print(f"📋 App ID: {app_id[:10]}..." if app_id else "❌ App ID: 未设置")
        print(f"🔑 App Secret: {'✅ 已设置' if app_secret else '❌ 未设置'}")
        print(f"📄 配置文件大小: {format_size(get_file_size(config_file))}")
        
        # 尝试测试连接
        try:
            from feishu_manager import FeishuManager
            manager = FeishuManager()
            manager._get_access_token()
            print("✅ 飞书 API 连接测试: 成功")
        except Exception as e:
            print(f"⚠️ 飞书 API 连接测试: 失败 ({str(e)[:50]})")
            
    except Exception as e:
        print(f"❌ 读取 feishu_config.json 失败: {e}")

def check_cache_files():
    """检查缓存文件"""
    print("\n" + "="*70)
    print("💾 缓存文件状态")
    print("="*70)
    
    cache_files = {
        'CoinGecko 缓存': 'coingecko_market_data_cache.json',
        '每日涨幅历史': 'daily_gainers_history.json',
    }
    
    total_size = 0
    for name, filename in cache_files.items():
        if os.path.exists(filename):
            size = get_file_size(filename)
            total_size += size
            
            # 尝试读取 JSON 以获取更多信息
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        count = len(data)
                        print(f"✅ {name}: {format_size(size)} ({count} 条记录)")
                    elif isinstance(data, dict):
                        count = len(data)
                        print(f"✅ {name}: {format_size(size)} ({count} 个键)")
                    else:
                        print(f"✅ {name}: {format_size(size)}")
            except:
                print(f"✅ {name}: {format_size(size)}")
        else:
            print(f"❌ {name}: 文件不存在")
    
    print(f"\n📊 缓存总大小: {format_size(total_size)}")

def check_output_directories():
    """检查输出目录"""
    print("\n" + "="*70)
    print("📁 输出目录统计")
    print("="*70)
    
    # 查找所有输出目录
    output_dirs = glob.glob('币安代币分析结果_*')
    output_dirs.sort(reverse=True)  # 最新的在前
    
    if not output_dirs:
        print("❌ 未找到输出目录")
        return
    
    print(f"📊 总输出目录数: {len(output_dirs)}")
    
    # 显示最近 5 个目录
    print(f"\n📋 最近 5 个输出目录:")
    total_size = 0
    for i, dir_path in enumerate(output_dirs[:5], 1):
        try:
            dir_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(dir_path)
                for filename in filenames
            )
            total_size += dir_size
            
            # 获取目录创建时间（使用修改时间作为近似值）
            mtime = os.path.getmtime(dir_path)
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"   {i}. {dir_path}")
            print(f"      大小: {format_size(dir_size)}")
            print(f"      时间: {mtime_str}")
        except Exception as e:
            print(f"   {i}. {dir_path} (无法读取: {e})")
    
    # 计算总大小
    print(f"\n📊 所有输出目录总大小: {format_size(total_size)}")
    
    # 统计各类型文件
    excel_count = 0
    csv_count = 0
    log_count = 0
    
    for dir_path in output_dirs:
        excel_files = glob.glob(os.path.join(dir_path, '**/*.xlsx'), recursive=True)
        csv_files = glob.glob(os.path.join(dir_path, '**/*.csv'), recursive=True)
        log_files = glob.glob(os.path.join(dir_path, '**/*.log'), recursive=True)
        
        excel_count += len(excel_files)
        csv_count += len(csv_files)
        log_count += len(log_files)
    
    print(f"\n📄 文件统计:")
    print(f"   Excel 文件: {excel_count} 个")
    print(f"   CSV 文件: {csv_count} 个")
    print(f"   日志文件: {log_count} 个")

def check_log_files():
    """检查日志文件"""
    print("\n" + "="*70)
    print("📝 日志文件状态")
    print("="*70)
    
    log_files = {
        '调度器日志': 'simple_scheduler.log',
        '调度器启动日志': 'simple_scheduler_startup.log',
        '调度器输出': 'simple_scheduler_output.log',
        '今日调度日志': 'scheduler_today.log',
    }
    
    for name, filename in log_files.items():
        if os.path.exists(filename):
            size = get_file_size(filename)
            try:
                mtime = os.path.getmtime(filename)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # 尝试读取最后几行
                try:
                    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        last_line = lines[-1].strip() if lines else "空文件"
                        print(f"✅ {name}: {format_size(size)}")
                        print(f"   最后更新: {mtime_str}")
                        print(f"   最后一行: {last_line[:80]}...")
                except:
                    print(f"✅ {name}: {format_size(size)}")
            except:
                print(f"✅ {name}: {format_size(size)}")
        else:
            print(f"❌ {name}: 文件不存在")

def check_config_files():
    """检查配置文件"""
    print("\n" + "="*70)
    print("⚙️ 配置文件状态")
    print("="*70)
    
    config_files = {
        '主配置': 'config.json',
        '飞书配置': 'feishu_config.json',
        '飞书表格配置': 'feishu_spreadsheet_config.json',
        'Telegram 配置': 'telegram_config.json',
        'OAuth 凭据': 'oauth_credentials.json',
    }
    
    for name, filename in config_files.items():
        if os.path.exists(filename):
            size = get_file_size(filename)
            print(f"✅ {name}: {format_size(size)}")
        else:
            print(f"⚠️ {name}: 不存在")

def check_dependencies():
    """检查依赖包"""
    print("\n" + "="*70)
    print("📦 Python 依赖状态")
    print("="*70)
    
    required_packages = [
        'pandas',
        'numpy',
        'requests',
        'gspread',
        'google-auth',
        'google-auth-oauthlib',
        'openpyxl',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未安装)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ 缺少 {len(missing)} 个依赖包")
        print("   运行: pip install -r requirements.txt")

def main():
    """主函数"""
    print("="*70)
    print("📊 币安代币筛选器 - 使用统计检查")
    print("="*70)
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查各项
    check_oauth_token()
    check_feishu_config()
    check_cache_files()
    check_output_directories()
    check_log_files()
    check_config_files()
    check_dependencies()
    
    print("\n" + "="*70)
    print("✅ 检查完成")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

