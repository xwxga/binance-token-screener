#!/usr/bin/env python3
"""
诊断和修复 OAuth token 权限范围问题
用于解决 Docker 环境中的 ACCESS_TOKEN_SCOPE_INSUFFICIENT 错误
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# 必需的权限范围
REQUIRED_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

TOKEN_FILE = 'token.json'
CREDS_FILE = 'oauth_credentials.json'

def check_token_scopes():
    """检查当前 token.json 中的权限范围"""
    print("🔍 检查 OAuth token 权限范围...")
    print("=" * 70)
    
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ 未找到 {TOKEN_FILE} 文件")
        return False, None
    
    try:
        # 加载 token
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, REQUIRED_SCOPES)
        
        # 获取 token 中的 scopes
        token_data = json.load(open(TOKEN_FILE, 'r'))
        token_scopes = token_data.get('scopes', [])
        
        print(f"📋 当前 token.json 中的权限范围:")
        for scope in token_scopes:
            print(f"   ✅ {scope}")
        
        print(f"\n📋 代码要求的权限范围:")
        for scope in REQUIRED_SCOPES:
            print(f"   {'✅' if scope in token_scopes else '❌'} {scope}")
        
        # 检查是否缺少必需的权限
        missing_scopes = [s for s in REQUIRED_SCOPES if s not in token_scopes]
        
        if missing_scopes:
            print(f"\n⚠️ 缺少以下必需的权限范围:")
            for scope in missing_scopes:
                print(f"   ❌ {scope}")
            return False, missing_scopes
        else:
            print(f"\n✅ 所有必需的权限范围都已包含")
            return True, None
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False, None

def fix_token_scopes():
    """修复 token 权限范围问题"""
    print("\n🔧 开始修复 OAuth token 权限范围...")
    print("=" * 70)
    
    # 检查凭据文件
    if not os.path.exists(CREDS_FILE):
        print(f"❌ 未找到 {CREDS_FILE} 文件")
        print("请确保 oauth_credentials.json 文件存在")
        return False
    
    # 备份旧 token
    if os.path.exists(TOKEN_FILE):
        backup_file = f"{TOKEN_FILE}.backup"
        print(f"💾 备份旧 token 到 {backup_file}...")
        import shutil
        shutil.copy(TOKEN_FILE, backup_file)
        print("✅ 备份完成")
    
    print("\n🔑 开始重新授权流程...")
    print("📌 重要提示:")
    print("  1. 浏览器将自动打开")
    print("  2. 请选择您的 Google 账户")
    print("  3. 点击'继续'授予权限")
    print("  4. 确保选择所有请求的权限（特别是 Google Sheets 和 Drive）")
    print("  5. 完成后返回此窗口")
    print("-" * 70)
    
    try:
        # 创建 OAuth 流程
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDS_FILE, 
            REQUIRED_SCOPES
        )
        
        # 运行授权流程
        # 注意：在 Docker 环境中，可能需要使用不同的方法
        # 如果 run_local_server 不工作，可以尝试其他方法
        print("\n🌐 启动本地服务器进行授权...")
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',  # 强制显示同意屏幕，确保获取所有权限
            access_type='offline',  # 确保获取刷新令牌
            include_granted_scopes='true'  # 包含所有授权的作用域
        )
        
        # 保存新令牌
        with open(TOKEN_FILE, 'w') as token:
            token_data = json.loads(creds.to_json())
            
            # 验证 scopes
            if 'scopes' in token_data:
                print(f"\n✅ 新 token 包含的权限范围:")
                for scope in token_data['scopes']:
                    print(f"   ✅ {scope}")
            
            token.write(json.dumps(token_data, indent=2))
        
        print(f"\n✅ 授权成功!")
        print(f"💾 新令牌已保存到: {os.path.abspath(TOKEN_FILE)}")
        
        # 验证刷新令牌
        if creds.refresh_token:
            print("✅ 已获取刷新令牌（可自动刷新）")
        else:
            print("⚠️ 未获取刷新令牌（可能需要定期重新授权）")
            print("   提示：如果之前已经授权过，可能需要先撤销授权")
            print("   访问: https://myaccount.google.com/permissions")
        
        if hasattr(creds, 'expiry') and creds.expiry:
            print(f"⏰ 令牌过期时间: {creds.expiry}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 授权失败: {e}")
        print("\n💡 Docker 环境故障排除:")
        print("  1. 确保端口 8080 可以访问（可能需要端口映射）")
        print("  2. 如果无法使用浏览器，可以尝试以下方法:")
        print("     a. 在本地机器上运行此脚本生成 token.json")
        print("     b. 将生成的 token.json 复制到 Docker 容器中")
        print("  3. 确保 oauth_credentials.json 文件正确")
        print("  4. 检查网络连接")
        
        return False

def main():
    """主函数"""
    print("🔐 OAuth Token 权限范围诊断和修复工具")
    print("=" * 70)
    print("此工具用于解决 Docker 环境中的权限范围不足问题")
    print("=" * 70)
    
    # 检查当前 token
    is_valid, missing_scopes = check_token_scopes()
    
    if is_valid:
        print("\n✅ Token 权限范围正常，无需修复")
        return
    
    if missing_scopes:
        print(f"\n⚠️ 发现权限范围问题，需要重新授权")
        choice = input("\n是否立即修复? (y/n, 默认y): ").strip().lower()
        
        if choice != 'n':
            success = fix_token_scopes()
            if success:
                print("\n🎉 修复完成!")
                print("现在可以重新运行主程序了")
            else:
                print("\n❌ 修复失败，请查看上面的错误信息")
        else:
            print("\n💡 手动修复步骤:")
            print("  1. 删除或重命名 token.json 文件")
            print("  2. 运行: python oauth_setup_enhanced.py")
            print("  3. 或者运行: python fix_oauth_token.py")
    else:
        print("\n⚠️ 无法检查 token，可能需要重新授权")
        choice = input("\n是否尝试重新授权? (y/n, 默认y): ").strip().lower()
        
        if choice != 'n':
            fix_token_scopes()

if __name__ == "__main__":
    main()


