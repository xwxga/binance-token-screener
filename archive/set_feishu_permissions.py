#!/usr/bin/env python3
"""
设置飞书表格权限 - 正确的API格式
"""

import requests
import json

def set_spreadsheet_permissions(spreadsheet_token, user_emails=None, make_public=False):
    """
    设置飞书表格权限
    
    Args:
        spreadsheet_token: 表格token
        user_emails: 要添加的用户邮箱列表
        make_public: 是否设置为公开（任何人可查看/编辑）
    """
    # 1. 获取token
    with open('feishu_config.json', 'r') as f:
        config = json.load(f)
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={
        "app_id": config['app_id'],
        "app_secret": config['app_secret']
    })
    
    token = response.json().get('tenant_access_token')
    print(f"✅ Token获取成功")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 方法1: 添加协作者（通过邮箱）
    if user_emails:
        print("\n📝 添加协作者:")
        for email in user_emails:
            url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{spreadsheet_token}/members"
            
            data = {
                "type": "user",  # 用户类型
                "member_id": email,  # 使用邮箱作为ID
                "member_type": "email",  # 成员类型为邮箱
                "perm": "edit"  # 编辑权限
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"   ✅ 成功添加: {email}")
                else:
                    print(f"   ❌ 添加失败 {email}: {result.get('msg')}")
            else:
                print(f"   ❌ HTTP错误 {email}: {response.status_code}")
    
    # 方法2: 获取分享链接设置
    print("\n📝 获取分享链接:")
    
    # 创建分享链接
    url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{spreadsheet_token}/public"
    
    # 设置为链接分享-可编辑
    data = {
        "external_access_entity": "open",  # 开放外部访问
        "security_entity": "anyone_editable",  # 任何人可编辑
        "comment_entity": "anyone_can_comment",  # 任何人可评论
        "share_entity": "anyone",  # 任何人
        "link_share_entity": "anyone_editable",  # 链接分享-任何人可编辑
        "invite_external": True  # 允许邀请外部用户
    }
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            print(f"   ✅ 分享链接设置成功")
        else:
            print(f"   ❌ 设置失败: {result.get('msg')}")
    else:
        # 如果PATCH失败，尝试PUT
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print(f"   ✅ 分享链接设置成功")
            else:
                print(f"   ❌ 设置失败: {result.get('msg')}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            
            # 尝试简单的设置
            print("\n   尝试简单设置...")
            simple_data = {
                "link_share_entity": "anyone_editable"
            }
            response = requests.patch(url, headers=headers, json=simple_data)
            if response.status_code == 200:
                print(f"   ✅ 简单设置成功")
    
    # 方法3: 查询当前权限
    print("\n📝 查询当前权限:")
    url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{spreadsheet_token}/members?type=file"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            members = result.get('data', {}).get('items', [])
            if members:
                print(f"   找到 {len(members)} 个权限设置:")
                for member in members:
                    print(f"     - {member}")
            else:
                print("   暂无权限设置")
    
    return f"https://ai1rvq4k35h.feishu.cn/sheets/{spreadsheet_token}"

def main():
    print("="*60)
    print("飞书表格权限设置工具")
    print("="*60)
    
    # 创建测试表格
    with open('feishu_config.json', 'r') as f:
        config = json.load(f)
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={
        "app_id": config['app_id'],
        "app_secret": config['app_secret']
    })
    
    token = response.json().get('tenant_access_token')
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 创建表格
    url = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets"
    response = requests.post(url, headers=headers, json={"title": "权限测试表格"})
    
    result = response.json()
    spreadsheet_token = result['data']['spreadsheet']['spreadsheet_token']
    print(f"✅ 测试表格创建成功: {spreadsheet_token}")
    
    # 设置权限
    # 如果你有特定用户的邮箱，可以添加：
    # user_emails = ["user1@example.com", "user2@example.com"]
    user_emails = []  # 暂时为空，需要时添加
    
    share_url = set_spreadsheet_permissions(
        spreadsheet_token,
        user_emails=user_emails,
        make_public=True
    )
    
    print(f"\n🔗 表格链接: {share_url}")
    print("\n提示:")
    print("1. 飞书表格的权限可能受企业管理员设置限制")
    print("2. 如需添加特定用户，请提供他们的飞书邮箱")
    print("3. 分享链接后，其他人可以通过链接访问和编辑")

if __name__ == "__main__":
    main()