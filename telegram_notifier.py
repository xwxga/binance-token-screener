#!/usr/bin/env python3
"""
Telegram Notifier - 发送每日运行日志到Telegram
"""

import os
import json
import requests
import logging
from datetime import datetime
import glob
from typing import List, Dict, Optional, Tuple

class TelegramNotifier:
    def __init__(self, config_file='telegram_config.json'):
        """初始化Telegram通知器"""
        self.config_file = config_file
        self.config = self.load_config()
        self.logger = self.setup_logger()
        self.project_path = "/Users/wenxiangxu/Desktop/alpha_team_code/binance_token_screener"
        
    def setup_logger(self):
        """设置日志记录器"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def load_config(self) -> Dict:
        """加载Telegram配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建默认配置
            default_config = {
                "bot_token": "8169474631:AAGJzotGIacWhBwi943mj_Wq1lus1hc3GpU",
                "chat_id": "",  # 需要通过setup_telegram.py获取
                "enabled": True
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            self.logger.warning(f"创建了配置文件 {self.config_file}，请运行 setup_telegram.py 获取chat_id")
            return default_config
    
    def get_today_logs(self) -> Tuple[List[str], Optional[str], Optional[str]]:
        """获取今天的日志文件和结果文件"""
        today = datetime.now().strftime('%Y%m%d')
        log_files = []
        excel_file = None
        feishu_url = None
        
        # 1. 主程序运行日志
        analysis_folder = f"{self.project_path}/币安代币分析结果_{today}"
        if os.path.exists(analysis_folder):
            # 获取日志文件
            log_folder = os.path.join(analysis_folder, "日志文件")
            if os.path.exists(log_folder):
                logs = glob.glob(os.path.join(log_folder, "*.log"))
                log_files.extend(logs)
            
            # 获取Excel文件
            excel_folder = os.path.join(analysis_folder, "Excel文件")
            if os.path.exists(excel_folder):
                excel_files = glob.glob(os.path.join(excel_folder, "*.xlsx"))
                if excel_files:
                    excel_file = max(excel_files, key=os.path.getctime)
        
        # 2. 调度器日志
        scheduler_log = f"{self.project_path}/simple_scheduler.log"
        if os.path.exists(scheduler_log):
            # 只读取今天的部分
            today_str = datetime.now().strftime('%Y-%m-%d')
            temp_log = f"{self.project_path}/scheduler_today.log"
            with open(scheduler_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                today_lines = [line for line in lines if today_str in line or not line.startswith('20')]
                if today_lines:
                    with open(temp_log, 'w', encoding='utf-8') as tf:
                        tf.writelines(today_lines[-500:])  # 最多500行
                    log_files.append(temp_log)
        
        # 3. 从日志中提取飞书URL
        if log_files:
            feishu_url = self.extract_feishu_url(log_files)
        
        return log_files, excel_file, feishu_url
    
    def extract_feishu_url(self, log_files: List[str]) -> Optional[str]:
        """从日志文件中提取飞书URL"""
        import re
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 查找飞书URL
                    urls = re.findall(r'https://[^\s]+feishu[^\s]+sheets[^\s]+', content)
                    if urls:
                        return urls[-1]  # 返回最后一个URL
            except Exception as e:
                continue
        return None
    
    def analyze_logs(self, log_files: List[str]) -> Dict:
        """分析日志内容，提取关键信息"""
        stats = {
            'errors': [],
            'warnings': [],
            'success': [],
            'total_tokens': 0,
            'run_time': None,
            'status': 'unknown'
        }
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    # 提取错误
                    if 'ERROR' in line or '❌' in line:
                        stats['errors'].append(line.strip())
                    # 提取警告
                    elif 'WARNING' in line or '⚠️' in line:
                        stats['warnings'].append(line.strip())
                    # 提取成功信息
                    elif any(kw in line for kw in ['成功', '完成', '✅', 'SUCCESS']):
                        stats['success'].append(line.strip())
                    
                    # 提取代币数量
                    if '现货代币数量:' in line or 'spot_count:' in line:
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            stats['total_tokens'] = int(numbers[0])
                    
                    # 提取运行时间
                    if '耗时' in line or 'elapsed' in line:
                        stats['run_time'] = line.strip()
                    
                    # 判断整体状态
                    if '运行成功' in line or '执行成功' in line:
                        stats['status'] = 'success'
                    elif '运行失败' in line or '执行失败' in line:
                        stats['status'] = 'failed'
                        
            except Exception as e:
                self.logger.error(f"分析日志文件失败 {log_file}: {e}")
        
        # 根据错误数判断状态
        if not stats['errors'] and stats['success']:
            stats['status'] = 'success'
        elif stats['errors']:
            stats['status'] = 'warning'
        
        return stats
    
    def format_message(self, stats: Dict, excel_file: Optional[str], feishu_url: Optional[str]) -> str:
        """格式化消息内容"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 状态图标
        status_icon = {
            'success': '✅',
            'warning': '⚠️',
            'failed': '❌',
            'unknown': '❓'
        }.get(stats['status'], '❓')
        
        # 构建消息
        message = f"""📊 **币安代币筛选器 - 每日报告**
📅 {now}

{status_icon} **状态**: {self._get_status_text(stats['status'])}"""
        
        # 添加运行时间
        if stats['run_time']:
            message += f"\n⏱️ **耗时**: {stats['run_time']}"
        
        # 添加分析数量
        if stats['total_tokens'] > 0:
            message += f"\n📈 **分析代币**: {stats['total_tokens']}个"
        
        # 添加飞书链接
        if feishu_url:
            message += f"\n\n📋 **飞书表格**:\n{feishu_url}"
        
        # 添加Excel文件信息
        if excel_file:
            message += f"\n\n📁 **Excel文件**: {os.path.basename(excel_file)}"
        
        # 添加错误和警告统计
        message += f"\n\n📊 **统计信息**:"
        message += f"\n✅ 成功操作: {len(stats['success'])}个"
        message += f"\n⚠️ 警告: {len(stats['warnings'])}个"
        message += f"\n❌ 错误: {len(stats['errors'])}个"
        
        # 如果有错误，显示前3个
        if stats['errors']:
            message += "\n\n**❌ 错误详情** (前3条):"
            for error in stats['errors'][:3]:
                # 截断过长的错误信息
                error_text = error[:150] + '...' if len(error) > 150 else error
                message += f"\n• {error_text}"
        
        # 如果有警告，显示前2个
        if stats['warnings'] and len(stats['warnings']) <= 5:
            message += "\n\n**⚠️ 警告详情**:"
            for warning in stats['warnings'][:2]:
                warning_text = warning[:150] + '...' if len(warning) > 150 else warning
                message += f"\n• {warning_text}"
        
        return message
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'success': '运行成功',
            'warning': '运行完成（有警告）',
            'failed': '运行失败',
            'unknown': '状态未知'
        }
        return status_map.get(status, '状态未知')
    
    def send_message(self, text: str, parse_mode: str = 'Markdown') -> bool:
        """发送文本消息到Telegram"""
        if not self.config.get('enabled', False):
            self.logger.info("Telegram通知已禁用")
            return False
        
        if not self.config.get('chat_id'):
            self.logger.error("未配置chat_id，请运行 python setup_telegram.py")
            return False
        
        url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
        data = {
            'chat_id': self.config['chat_id'],
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                self.logger.info("✅ Telegram消息发送成功")
                return True
            else:
                self.logger.error(f"❌ Telegram消息发送失败: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Telegram消息发送异常: {e}")
            return False
    
    def send_document(self, file_path: str, caption: str = None) -> bool:
        """发送文件到Telegram"""
        if not self.config.get('enabled', False):
            return False
        
        if not self.config.get('chat_id'):
            self.logger.error("未配置chat_id")
            return False
        
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        # 检查文件大小（Telegram限制50MB）
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        if file_size > 50:
            self.logger.warning(f"文件太大 ({file_size:.1f}MB)，跳过发送")
            return False
        
        url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendDocument"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'chat_id': self.config['chat_id'],
                    'caption': caption or f"📎 {os.path.basename(file_path)}"
                }
                response = requests.post(url, data=data, files=files, timeout=30)
                
            if response.status_code == 200:
                self.logger.info(f"✅ 文件发送成功: {os.path.basename(file_path)}")
                return True
            else:
                self.logger.error(f"❌ 文件发送失败: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 文件发送异常: {e}")
            return False
    
    def send_daily_report(self, send_files: bool = True) -> bool:
        """发送每日报告"""
        self.logger.info("开始准备每日报告...")
        
        # 获取日志和文件
        log_files, excel_file, feishu_url = self.get_today_logs()
        
        if not log_files and not excel_file:
            self.logger.warning("没有找到今天的运行记录")
            # 发送一个简单的通知
            self.send_message("📊 币安代币筛选器\n\n⚠️ 今天没有运行记录")
            return False
        
        # 分析日志
        stats = self.analyze_logs(log_files)
        
        # 格式化消息
        message = self.format_message(stats, excel_file, feishu_url)
        
        # 发送主消息
        success = self.send_message(message)
        
        # 发送日志文件（如果启用）
        if send_files and success:
            # 选择最重要的日志文件发送
            for log_file in log_files[:2]:  # 最多发送2个日志文件
                if os.path.exists(log_file):
                    file_size = os.path.getsize(log_file) / (1024 * 1024)
                    if file_size < 10:  # 小于10MB才发送
                        caption = f"📝 日志文件: {os.path.basename(log_file)}"
                        self.send_document(log_file, caption)
            
            # 清理临时文件
            temp_log = f"{self.project_path}/scheduler_today.log"
            if os.path.exists(temp_log):
                os.remove(temp_log)
        
        return success
    
    def send_error_alert(self, error_message: str) -> bool:
        """发送错误警报（用于紧急通知）"""
        message = f"""🚨 **紧急警报**
        
币安代币筛选器运行出错！

❌ **错误信息**:
{error_message}

🕐 **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查程序日志了解详情。"""
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """测试连接"""
        test_message = f"""🧪 **测试消息**

✅ Telegram Bot连接成功！
🤖 Bot Token: {self.config['bot_token'][:20]}...
💬 Chat ID: {self.config.get('chat_id', '未设置')}
🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

币安代币筛选器Telegram通知已配置成功。"""
        
        return self.send_message(test_message)

def main():
    """主函数 - 用于测试和手动发送"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Telegram通知器')
    parser.add_argument('--test', action='store_true', help='测试连接')
    parser.add_argument('--send', action='store_true', help='发送今日报告')
    parser.add_argument('--error', type=str, help='发送错误警报')
    args = parser.parse_args()
    
    notifier = TelegramNotifier()
    
    if args.test:
        if notifier.test_connection():
            print("✅ 测试成功")
        else:
            print("❌ 测试失败")
    elif args.send:
        if notifier.send_daily_report():
            print("✅ 报告发送成功")
        else:
            print("❌ 报告发送失败")
    elif args.error:
        if notifier.send_error_alert(args.error):
            print("✅ 错误警报发送成功")
        else:
            print("❌ 错误警报发送失败")
    else:
        print("使用方法:")
        print("  --test   测试连接")
        print("  --send   发送今日报告")
        print("  --error  发送错误警报")

if __name__ == "__main__":
    main()