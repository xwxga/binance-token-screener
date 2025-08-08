#!/usr/bin/env python3
"""
增强版OAuth设置脚本
确保获取刷新令牌以避免频繁重新授权
Enhanced OAuth setup script to ensure refresh token is obtained
"""

from __future__ import print_function
import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth 2.0 作用域
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def setup_oauth():
    """设置OAuth认证"""
    print("🔐 币安代币筛选器 - OAuth设置工具 (增强版)")
    print("=" * 60)
    print("📋 此工具将帮助您:")
    print("  1. 设置Google Sheets API访问权限")
    print("  2. 生成长期有效的刷新令牌")
    print("  3. 避免频繁重新授权")
    print("=" * 60)
    
    creds = None
    
    # 检查现有令牌
    if os.path.exists('token.json'):
        print("\n📄 发现现有token.json文件")
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            print("✅ 成功加载现有令牌")
            
            # 显示令牌信息
            print(f"  - 令牌有效: {creds.valid}")
            print(f"  - 令牌过期: {creds.expired}")
            print(f"  - 有刷新令牌: {creds.refresh_token is not None}")
            
            if creds.valid:
                choice = input("\n现有令牌仍然有效，是否要重新授权? (y/n): ")
                if choice.lower() != 'y':
                    print("✅ 保留现有令牌")
                    return
            elif creds.expired and creds.refresh_token:
                print("\n🔄 令牌已过期，尝试刷新...")
                try:
                    creds.refresh(Request())
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                    print("✅ 令牌刷新成功!")
                    return
                except Exception as e:
                    print(f"❌ 刷新失败: {e}")
                    print("需要重新授权...")
                    
        except Exception as e:
            print(f"⚠️ 读取现有令牌失败: {e}")
            print("将创建新的令牌...")
    
    # 检查凭据文件
    if not os.path.exists('oauth_credentials.json'):
        print("\n❌ 错误: 未找到 oauth_credentials.json 文件")
        print("\n📝 请按以下步骤操作:")
        print("1. 访问 https://console.cloud.google.com/")
        print("2. 创建新项目或选择现有项目")
        print("3. 启用 Google Sheets API 和 Google Drive API")
        print("4. 创建 OAuth 2.0 客户端ID")
        print("5. 下载凭据JSON文件并重命名为 oauth_credentials.json")
        print("6. 将文件放在当前目录下")
        return
    
    # 创建OAuth流程
    print("\n🔑 开始OAuth授权流程...")
    print("重要: 确保在授权时选择所有请求的权限")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'oauth_credentials.json', 
            SCOPES
        )
        
        # 关键参数确保获取刷新令牌
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',  # 强制显示权限同意屏幕
            access_type='offline',  # 获取刷新令牌
            include_granted_scopes='true'  # 包含所有授权的作用域
        )
        
        # 保存令牌
        with open('token.json', 'w') as token:
            token_data = json.loads(creds.to_json())
            
            # 验证刷新令牌
            if 'refresh_token' not in token_data or not token_data['refresh_token']:
                print("\n⚠️ 警告: 未获取到刷新令牌!")
                print("可能需要:")
                print("  1. 从Google账户中移除应用授权")
                print("  2. 重新运行此脚本")
            else:
                print("\n✅ 成功获取刷新令牌!")
            
            token.write(json.dumps(token_data, indent=2))
        
        print("\n✅ OAuth设置完成!")
        print(f"💾 令牌已保存到: {os.path.abspath('token.json')}")
        
        # 显示令牌信息
        if hasattr(creds, 'expiry') and creds.expiry:
            print(f"⏰ 令牌过期时间: {creds.expiry}")
        print(f"🔄 刷新令牌: {'已获取' if creds.refresh_token else '未获取'}")
        
    except Exception as e:
        print(f"\n❌ OAuth设置失败: {e}")
        print("\n💡 常见问题解决:")
        print("  1. 确保已安装所有依赖: pip install google-auth google-auth-oauthlib google-auth-httplib2")
        print("  2. 检查oauth_credentials.json文件是否正确")
        print("  3. 确保端口8080未被占用")
        print("  4. 尝试使用其他浏览器")
        return
    
    # 测试API访问
    print("\n🧪 测试Google Sheets API访问...")
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # 创建测试表格
        spreadsheet = {
            'properties': {
                'title': f'OAuth测试_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            }
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        print(f"✅ API测试成功! 创建了测试表格: {result.get('properties', {}).get('title')}")
        print(f"📊 表格URL: {result.get('spreadsheetUrl')}")
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        print("请检查API是否已启用")
    
    print("\n🎉 设置完成!")
    print("您现在可以运行主程序了: python binance_token_screener_v1.1.py")
    
    # 提供额外建议
    print("\n💡 重要提示:")
    print("  1. 请妥善保管token.json文件")
    print("  2. 不要将token.json提交到版本控制系统")
    print("  3. 如果长时间未使用(6个月+)，可能需要重新授权")
    print("  4. 建议定期运行主程序以保持令牌活跃")

def revoke_authorization():
    """撤销现有授权（用于故障排除）"""
    print("\n🔓 撤销现有授权...")
    
    if os.path.exists('token.json'):
        try:
            os.remove('token.json')
            print("✅ 已删除token.json")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
    
    print("\n💡 下一步:")
    print("  1. 访问: https://myaccount.google.com/permissions")
    print("  2. 找到并撤销此应用的访问权限")
    print("  3. 重新运行此脚本进行授权")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--revoke':
        revoke_authorization()
    else:
        setup_oauth()

if __name__ == '__main__':
    main()