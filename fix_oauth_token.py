#!/usr/bin/env python3
"""
修复OAuth令牌过期问题
非交互式版本
"""

import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# 配置
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
TOKEN_FILE = 'token.json'
CREDS_FILE = 'oauth_credentials.json'

def main():
    """主函数"""
    print("🚀 OAuth令牌修复工具")
    print("=" * 70)
    
    # 检查凭据文件
    if not os.path.exists(CREDS_FILE):
        print("❌ 缺少oauth_credentials.json文件")
        print("请先获取OAuth客户端凭据")
        return
    
    # 删除旧令牌
    if os.path.exists(TOKEN_FILE):
        print("🗑️ 删除旧的token.json文件...")
        os.remove(TOKEN_FILE)
        print("✅ 已删除旧令牌")
    
    print("\n🔑 开始新的授权流程...")
    print("📌 浏览器将自动打开，请完成以下步骤:")
    print("  1. 选择您的Google账户")
    print("  2. 点击'继续'授予权限")
    print("  3. 确保选择所有请求的权限")
    print("  4. 完成后返回此窗口")
    print("-" * 70)
    
    try:
        # 创建OAuth流程
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDS_FILE, 
            SCOPES
        )
        
        # 运行授权流程
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',  # 强制显示同意屏幕
            access_type='offline',  # 确保获取刷新令牌
            include_granted_scopes='true'
        )
        
        # 保存令牌
        with open(TOKEN_FILE, 'w') as token:
            token_data = json.loads(creds.to_json())
            token.write(json.dumps(token_data, indent=2))
        
        print("\n✅ 授权成功!")
        print(f"💾 新令牌已保存到: {os.path.abspath(TOKEN_FILE)}")
        
        # 验证令牌
        if creds.refresh_token:
            print("✅ 已获取刷新令牌（可自动刷新）")
        else:
            print("⚠️ 未获取刷新令牌（可能需要定期重新授权）")
        
        if hasattr(creds, 'expiry') and creds.expiry:
            print(f"⏰ 令牌过期时间: {creds.expiry}")
        
        print("\n🎉 修复完成!")
        print("您现在可以运行主程序了:")
        print("  python binance_token_screener_v1.1.py")
        
    except Exception as e:
        print(f"\n❌ 授权失败: {e}")
        print("\n💡 故障排除:")
        print("  1. 确保端口8080未被占用")
        print("  2. 检查oauth_credentials.json是否正确")
        print("  3. 尝试使用其他浏览器")
        print("  4. 确保网络连接正常")
        
        # 如果是端口占用问题，尝试其他端口
        if "address already in use" in str(e).lower():
            print("\n尝试使用其他端口:")
            print("  编辑此脚本，将port=8080改为port=8081或其他未占用端口")

if __name__ == "__main__":
    main()