#!/usr/bin/env python3
"""
Setup Telegram Bot - 获取chat_id并配置Telegram通知
"""

import json
import requests
import time
import os

BOT_TOKEN = "8169474631:AAGJzotGIacWhBwi943mj_Wq1lus1hc3GpU"
CONFIG_FILE = "telegram_config.json"

def get_bot_info():
    """获取Bot信息"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Bot连接成功!")
            print(f"🤖 Bot名称: @{bot_info.get('username')}")
            print(f"📝 Bot昵称: {bot_info.get('first_name')}")
            return bot_info
    print("❌ 无法连接到Bot")
    return None

def get_updates(offset=None):
    """获取Bot收到的消息"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {}
    if offset:
        params['offset'] = offset
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            return data.get('result', [])
    return []

def wait_for_message():
    """等待用户发送消息以获取chat_id"""
    print("\n" + "="*50)
    print("📱 请按以下步骤操作:")
    print("="*50)
    print("1. 打开Telegram")
    print("2. 搜索Bot: @binance_screener_bot (或使用您的bot用户名)")
    print("3. 点击 'Start' 或发送 /start")
    print("4. 发送任意消息（比如: 'Hello'）")
    print("\n⏳ 等待您的消息...")
    print("="*50)
    
    last_update_id = None
    attempts = 0
    max_attempts = 60  # 最多等待60秒
    
    while attempts < max_attempts:
        updates = get_updates(last_update_id)
        
        for update in updates:
            last_update_id = update.get('update_id') + 1
            
            # 获取消息信息
            message = update.get('message')
            if message:
                chat = message.get('chat')
                from_user = message.get('from')
                text = message.get('text', '')
                
                if chat:
                    chat_id = chat.get('id')
                    chat_type = chat.get('type')
                    
                    print(f"\n✅ 收到消息!")
                    print(f"👤 发送者: {from_user.get('first_name', '')} {from_user.get('last_name', '')}")
                    print(f"🆔 用户名: @{from_user.get('username', 'unknown')}")
                    print(f"💬 消息: {text}")
                    print(f"🔑 Chat ID: {chat_id}")
                    print(f"📍 聊天类型: {chat_type}")
                    
                    # 如果是@SeanXXu，自动确认
                    if from_user.get('username') == 'SeanXXu':
                        print("\n🎯 检测到目标用户 @SeanXXu!")
                        return str(chat_id)
                    
                    # 询问是否使用这个chat_id
                    confirm = input(f"\n是否使用这个Chat ID ({chat_id})? (y/n): ").strip().lower()
                    if confirm == 'y':
                        return str(chat_id)
        
        time.sleep(1)
        attempts += 1
        if attempts % 10 == 0:
            print(f"⏳ 已等待 {attempts} 秒...")
    
    print("\n⏰ 超时！请确保已向Bot发送消息")
    return None

def save_config(chat_id):
    """保存配置到文件"""
    config = {
        "bot_token": BOT_TOKEN,
        "chat_id": chat_id,
        "enabled": True
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ 配置已保存到 {CONFIG_FILE}")

def test_send_message(chat_id):
    """测试发送消息"""
    print("\n🧪 测试发送消息...")
    
    test_message = f"""🎉 恭喜！Telegram Bot配置成功！

🤖 Bot已准备就绪
📊 币安代币筛选器将在每次运行后发送报告到这里

配置信息:
• Chat ID: {chat_id}
• 通知状态: 已启用

您将收到:
• 每日运行报告
• 错误警报
• 运行统计

祝您交易愉快！🚀"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': test_message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ 测试消息发送成功！请检查Telegram")
        return True
    else:
        print(f"❌ 发送失败: {response.text}")
        return False

def main():
    """主函数"""
    print("🤖 Telegram Bot 设置向导")
    print("="*50)
    
    # 检查是否已有配置
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            existing_config = json.load(f)
            if existing_config.get('chat_id'):
                print(f"📌 发现现有配置:")
                print(f"   Chat ID: {existing_config['chat_id']}")
                print(f"   状态: {'启用' if existing_config.get('enabled') else '禁用'}")
                
                overwrite = input("\n是否要重新配置? (y/n): ").strip().lower()
                if overwrite != 'y':
                    # 测试现有配置
                    test = input("是否测试现有配置? (y/n): ").strip().lower()
                    if test == 'y':
                        test_send_message(existing_config['chat_id'])
                    return
    
    # 获取Bot信息
    bot_info = get_bot_info()
    if not bot_info:
        print("❌ 无法连接到Bot，请检查网络连接")
        return
    
    # 等待用户消息以获取chat_id
    chat_id = wait_for_message()
    
    if chat_id:
        # 保存配置
        save_config(chat_id)
        
        # 测试发送
        test_send_message(chat_id)
        
        print("\n" + "="*50)
        print("✅ 设置完成！")
        print("="*50)
        print("\n下一步:")
        print("1. 程序会在每次运行后自动发送报告")
        print("2. 可以运行 'python telegram_notifier.py --test' 测试")
        print("3. 可以运行 'python telegram_notifier.py --send' 手动发送今日报告")
    else:
        print("\n❌ 未能获取Chat ID")
        print("请重新运行此脚本并确保向Bot发送了消息")

if __name__ == "__main__":
    main()