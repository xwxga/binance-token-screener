#!/usr/bin/env python3
"""
简单的持续运行定时调度器 - 每天7:45自动执行币安代币筛选器
无需系统权限，只需要在后台持续运行
"""

import schedule
import time
import subprocess
import os
import sys
import logging
import json
import requests
from datetime import datetime, timedelta

class SimpleScheduler:
    def __init__(self):
        # 配置信息
        self.project_path = "/Users/wenxiangxu/Desktop/alpha_team_code/binance_token_screener"
        self.venv_path = "/Users/wenxiangxu/opt/anaconda3/envs/crypto_project"
        self.main_script = "binance_token_screener_v3.0.py"
        self.log_file = "simple_scheduler.log"
        
        # 代理配置（如果需要）
        self.proxy_config = self.load_proxy_config()
        
        # 运行统计
        self.run_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_run_time = None
        self.last_run_status = None
        
        # 设置日志
        self.setup_logging()
        
    def load_proxy_config(self):
        """加载代理配置"""
        try:
            config_file = os.path.join(self.project_path, "scheduler_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if config.get('proxy_settings', {}).get('enabled', False):
                    return {
                        'http': config['proxy_settings'].get('http_proxy'),
                        'https': config['proxy_settings'].get('https_proxy'),
                    }
        except Exception as e:
            print(f"⚠️ 加载代理配置失败: {e}")
        
        return {'http': None, 'https': None}
        
    def setup_logging(self):
        """设置日志记录"""
        log_path = os.path.join(self.project_path, self.log_file)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_network_connection(self):
        """检查网络连接"""
        try:
            test_urls = [
                "https://api.binance.com/api/v3/ping",
                "https://www.google.com"
            ]
            
            for url in test_urls:
                try:
                    if any(self.proxy_config.values()):
                        response = requests.get(url, proxies=self.proxy_config, timeout=10)
                    else:
                        response = requests.get(url, timeout=10)
                        
                    if response.status_code == 200:
                        self.logger.info(f"✅ 网络连接正常")
                        return True
                except:
                    continue
                    
            self.logger.error("❌ 网络连接失败")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 网络连接检查异常: {e}")
            return False
    
    def check_environment(self):
        """检查环境"""
        checks = [
            (os.path.exists(self.project_path), f"项目目录: {self.project_path}"),
            (os.path.exists(os.path.join(self.project_path, self.main_script)), f"主脚本: {self.main_script}"),
            (os.path.exists(self.venv_path), f"虚拟环境: {self.venv_path}"),
            (os.path.exists(os.path.join(self.venv_path, "bin", "python")), "Python可执行文件")
        ]
        
        for check, description in checks:
            if not check:
                self.logger.error(f"❌ {description} - 检查失败")
                return False
                
        self.logger.info("✅ 环境检查通过")
        return True
    
    def set_proxy_environment(self):
        """设置代理环境变量"""
        if any(self.proxy_config.values()):
            if self.proxy_config['http']:
                os.environ['HTTP_PROXY'] = self.proxy_config['http']
                os.environ['http_proxy'] = self.proxy_config['http']
                
            if self.proxy_config['https']:
                os.environ['HTTPS_PROXY'] = self.proxy_config['https']
                os.environ['https_proxy'] = self.proxy_config['https']
                
            self.logger.info(f"🌐 已设置代理: {self.proxy_config}")
        else:
            # 清除代理环境变量
            for var in ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']:
                if var in os.environ:
                    del os.environ[var]
            self.logger.info("🌐 使用直连")
    
    def run_main_script(self):
        """运行主脚本"""
        try:
            self.logger.info("🚀 开始执行币安代币筛选器...")
            
            # 设置代理环境变量
            self.set_proxy_environment()
            
            # 构建命令
            python_exe = os.path.join(self.venv_path, "bin", "python")
            script_path = os.path.join(self.project_path, self.main_script)
            
            # 添加 --auto 参数以跳过用户输入
            cmd = [python_exe, script_path, '--auto']
            
            # 执行命令
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode == 0:
                self.logger.info("✅ 脚本执行成功")
                # 只显示输出的最后部分
                if result.stdout:
                    output_lines = result.stdout.split('\n')
                    if len(output_lines) > 10:
                        self.logger.info("脚本输出（最后10行）:")
                        for line in output_lines[-10:]:
                            if line.strip():
                                self.logger.info(f"  {line}")
                return True
            else:
                self.logger.error(f"❌ 脚本执行失败，返回码: {result.returncode}")
                if result.stderr:
                    self.logger.error(f"错误输出: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ 脚本执行超时（30分钟）")
            return False
        except Exception as e:
            self.logger.error(f"❌ 脚本执行异常: {e}")
            return False
    
    def scheduled_job(self):
        """定时任务主函数"""
        self.run_count += 1
        self.last_run_time = datetime.now()
        
        self.logger.info("=" * 80)
        self.logger.info(f"🕐 开始执行第 {self.run_count} 次定时任务")
        self.logger.info(f"📅 执行时间: {self.last_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = False
        
        try:
            # 1. 检查网络连接
            if not self.check_network_connection():
                self.last_run_status = "网络连接失败"
                self.failure_count += 1
                return
            
            # 2. 检查环境
            if not self.check_environment():
                self.last_run_status = "环境检查失败"
                self.failure_count += 1
                return
            
            # 3. 运行主脚本
            if self.run_main_script():
                success = True
                self.success_count += 1
                self.last_run_status = "执行成功"
                self.logger.info("🎉 定时任务执行完成")
            else:
                self.last_run_status = "脚本执行失败"
                self.failure_count += 1
                        
        except Exception as e:
            self.last_run_status = f"异常: {e}"
            self.logger.error(f"❌ 定时任务执行异常: {e}")
            self.failure_count += 1
        
        finally:
            self.logger.info(f"📊 任务状态: {self.last_run_status}")
            self.logger.info(f"📈 统计: 总运行{self.run_count}次, 成功{self.success_count}次, 失败{self.failure_count}次")
            if self.run_count > 0:
                success_rate = (self.success_count / self.run_count) * 100
                self.logger.info(f"📈 成功率: {success_rate:.1f}%")
            self.logger.info("=" * 80)
    
    def get_status(self):
        """获取运行状态"""
        return {
            'run_count': self.run_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': f"{(self.success_count/self.run_count*100):.1f}%" if self.run_count > 0 else "0%",
            'last_run_time': self.last_run_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_run_time else None,
            'last_run_status': self.last_run_status,
            'next_run': schedule.next_run().strftime('%Y-%m-%d %H:%M:%S') if schedule.jobs else None,
            'proxy_enabled': any(self.proxy_config.values())
        }
    
    def start_scheduler(self):
        """启动定时调度器"""
        self.logger.info("🚀 启动简单定时调度器")
        self.logger.info(f"📁 项目路径: {self.project_path}")
        self.logger.info(f"🐍 虚拟环境: {self.venv_path}")
        self.logger.info(f"📄 主脚本: {self.main_script}")
        self.logger.info(f"⏰ 执行时间: 每天 07:45")
        self.logger.info(f"🌐 代理状态: {'启用' if any(self.proxy_config.values()) else '禁用'}")
        
        # 设置定时任务
        schedule.every().day.at("07:45").do(self.scheduled_job)
        
        self.logger.info("✅ 定时任务已设置")
        if schedule.jobs:
            self.logger.info(f"⏰ 下次执行时间: {schedule.next_run().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.logger.info("🔄 调度器开始运行，按 Ctrl+C 停止")
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ 收到停止信号，正在关闭调度器...")
        except Exception as e:
            self.logger.error(f"❌ 调度器运行异常: {e}")
        finally:
            self.logger.info("👋 调度器已停止")

def main():
    """主函数"""
    print("🎯 币安代币筛选器简单定时运行程序")
    print("=" * 50)

    # 创建调度器实例
    scheduler = SimpleScheduler()

    # 显示配置信息
    print(f"📁 项目路径: {scheduler.project_path}")
    print(f"🐍 虚拟环境: {scheduler.venv_path}")
    print(f"📄 主脚本: {scheduler.main_script}")
    print(f"⏰ 执行时间: 每天 07:45")
    print(f"🌐 代理状态: {'启用' if any(scheduler.proxy_config.values()) else '禁用'}")
    print(f"📝 日志文件: {scheduler.log_file}")

    # 检查是否为交互式运行
    if sys.stdin.isatty():
        # 交互式运行，询问是否立即测试
        try:
            test_now = input("\n是否立即执行一次测试？(y/n): ").lower().strip()
            if test_now == 'y':
                print("\n🧪 执行测试运行...")
                scheduler.scheduled_job()

                status = scheduler.get_status()
                print(f"\n📊 测试结果: {status['last_run_status']}")

                continue_schedule = input("\n是否继续启动定时调度？(y/n): ").lower().strip()
                if continue_schedule != 'y':
                    print("👋 程序退出")
                    return
        except (EOFError, KeyboardInterrupt):
            print("\n👋 程序退出")
            return
    else:
        # 非交互式运行（后台运行），直接启动
        print("\n🚀 检测到后台运行模式，直接启动调度器...")

    # 启动定时调度器
    print("\n🚀 启动定时调度器...")
    if sys.stdin.isatty():
        print("💡 提示: 保持此窗口运行，程序将在后台持续运行")
        print("💡 提示: 按 Ctrl+C 可以停止程序")
    else:
        print("💡 提示: 程序在后台运行，每天7:45自动执行")
    scheduler.start_scheduler()

if __name__ == "__main__":
    main()
