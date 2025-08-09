#!/usr/bin/env python3
"""
飞书电子表格管理器 - 简化版
用于币安代币筛选器v3.0的飞书表格集成
根据feishu_api_guide.md实现核心功能
"""

import requests
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Any

class FeishuManager:
    """
    飞书电子表格管理器
    替代Google Sheets功能，提供相同的接口
    """
    
    def __init__(self, config_file='feishu_config.json'):
        """初始化飞书管理器"""
        self.config_file = config_file
        self.access_token = None
        self.token_expires_at = 0
        self.base_url = "https://open.feishu.cn/open-apis"
        
        # 加载配置
        self._load_config()
        
        # API限制
        self.max_cells_per_request = 5000
        self.qps_limit = 20
        self.last_request_time = 0
        
        # 当前表格信息
        self.spreadsheet_token = None
        self.sheet_ids = {}  # sheet_name -> sheet_id mapping
        self.default_sheet_id = None  # 默认sheet的ID，需要删除
        
    def _load_config(self):
        """加载飞书配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.app_id = config.get('app_id')
                self.app_secret = config.get('app_secret')
                
            if not self.app_id or not self.app_secret:
                raise ValueError("缺少app_id或app_secret")
                
            print("🔐 飞书配置加载成功")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        except Exception as e:
            raise Exception(f"加载配置失败: {e}")
    
    def _rate_limit(self):
        """速率限制"""
        current_time = time.time()
        min_interval = 1.0 / self.qps_limit
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _get_access_token(self):
        """获取访问令牌"""
        current_time = time.time()
        
        # 如果token还有效，直接返回
        if self.access_token and current_time < self.token_expires_at:
            return self.access_token
        
        self._rate_limit()
        
        # 获取新的access token
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                expire = result.get("expire", 7200)
                self.token_expires_at = current_time + expire - 300  # 提前5分钟刷新
                print("✅ 飞书访问令牌获取成功")
                return self.access_token
            else:
                raise Exception(f"获取token失败: {result.get('msg')}")
                
        except Exception as e:
            raise Exception(f"获取访问令牌失败: {e}")
    
    def create_spreadsheet(self, title: str) -> str:
        """
        创建新的电子表格
        
        Args:
            title: 表格标题
            
        Returns:
            spreadsheet_token
        """
        self._get_access_token()
        self._rate_limit()
        
        url = f"{self.base_url}/sheets/v3/spreadsheets"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"title": title}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 0:
                spreadsheet = result.get("data", {}).get("spreadsheet", {})
                self.spreadsheet_token = spreadsheet.get("spreadsheet_token")
                
                # 获取默认创建的sheet信息
                sheets = spreadsheet.get("sheets", {})
                if sheets:
                    # 保存默认sheet的ID，稍后删除
                    self.default_sheet_id = list(sheets.keys())[0]
                else:
                    self.default_sheet_id = None
                
                print(f"✅ 创建飞书表格: {title}")
                print(f"📎 表格Token: {self.spreadsheet_token}")
                return self.spreadsheet_token
            else:
                raise Exception(f"创建表格失败: {result.get('msg')}")
                
        except Exception as e:
            raise Exception(f"创建电子表格失败: {e}")
    
    def create_worksheet(self, sheet_name: str, row_count: int = 1000, column_count: int = 30) -> str:
        """
        创建新的工作表
        
        Args:
            sheet_name: 工作表名称
            row_count: 行数
            column_count: 列数
            
        Returns:
            sheet_id
        """
        if not self.spreadsheet_token:
            raise Exception("请先创建电子表格")
        
        self._get_access_token()
        self._rate_limit()
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "properties": {
                "title": sheet_name,  # 这个会被忽略，API会自动命名为Sheet2, Sheet3等
                "row_count": row_count,
                "column_count": column_count
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 0:
                sheet = result.get("data", {}).get("sheet", {})
                sheet_id = sheet.get("sheet_id")
                returned_title = sheet.get("title", "")  # 获取API返回的标题（如Sheet2）
                
                # 立即重命名为我们想要的名称
                if returned_title != sheet_name:
                    if self.update_sheet_properties(sheet_id, sheet_name):
                        print(f"  ✅ 创建工作表: {sheet_name}")
                    else:
                        print(f"  ⚠️ 创建工作表: {returned_title} (重命名失败，应为: {sheet_name})")
                else:
                    print(f"  ✅ 创建工作表: {sheet_name}")
                
                self.sheet_ids[sheet_name] = sheet_id
                return sheet_id
            else:
                raise Exception(f"创建工作表失败: {result.get('msg')}")
                
        except Exception as e:
            raise Exception(f"创建工作表 {sheet_name} 失败: {e}")
    
    def _prepare_data_for_feishu(self, df: pd.DataFrame) -> List[List[Any]]:
        """
        准备DataFrame数据用于飞书上传
        处理数据类型转换（布尔值、NaN等）
        
        Args:
            df: pandas DataFrame
            
        Returns:
            二维列表数据
        """
        data_list = []
        
        # 添加表头
        data_list.append(df.columns.tolist())
        
        # 转换数据行
        for _, row in df.iterrows():
            row_data = []
            for val in row.values:
                # 处理布尔值 - 转为字符串
                if isinstance(val, (bool, np.bool_)):
                    row_data.append(str(val))
                # 处理NaN和None - 转为空字符串
                elif pd.isna(val) or val is None:
                    row_data.append("")
                # 处理numpy类型
                elif isinstance(val, (np.integer, np.floating, np.int64, np.float64)):
                    # 处理inf和-inf
                    if np.isinf(val):
                        row_data.append("")
                    else:
                        # 转换numpy类型为Python原生类型
                        if isinstance(val, (np.integer, np.int64)):
                            row_data.append(int(val))
                        else:
                            row_data.append(float(val))
                # 其他类型保持原样
                else:
                    row_data.append(val)
            data_list.append(row_data)
        
        return data_list
    
    def write_data_to_sheet(self, sheet_name: str, df: pd.DataFrame) -> bool:
        """
        写入数据到工作表
        
        Args:
            sheet_name: 工作表名称
            df: 要写入的DataFrame
            
        Returns:
            是否成功
        """
        if not self.spreadsheet_token:
            raise Exception("请先创建电子表格")
        
        # 如果工作表不存在，先创建
        if sheet_name not in self.sheet_ids:
            row_count = max(1000, len(df) + 100)
            col_count = max(30, len(df.columns) + 5)
            self.create_worksheet(sheet_name, row_count, col_count)
        
        sheet_id = self.sheet_ids.get(sheet_name)
        if not sheet_id:
            print(f"    ❌ 无法获取工作表ID: {sheet_name}")
            return False
        
        # 准备数据
        data = self._prepare_data_for_feishu(df)
        
        # 计算范围 - 使用sheet_id格式
        end_col = self._number_to_column(len(df.columns))
        end_row = len(data)
        range_str = f"{sheet_id}!A1:{end_col}{end_row}"
        
        self._get_access_token()
        self._rate_limit()
        
        # 使用v2 API - 已验证可工作
        url = f"{self.base_url}/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_batch_update"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "valueRanges": [{
                "range": range_str,
                "values": data
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 0:
                print(f"    ✅ 数据写入: {sheet_name} ({len(df)}行 × {len(df.columns)}列)")
                return True
            else:
                print(f"    ❌ 写入失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            print(f"    ❌ 写入数据失败: {e}")
            return False
    
    def _number_to_column(self, n: int) -> str:
        """
        将数字转换为Excel列名（1->A, 27->AA）
        
        Args:
            n: 列号（从1开始）
            
        Returns:
            列名字符串
        """
        result = ""
        while n > 0:
            n -= 1
            result = chr(ord('A') + n % 26) + result
            n //= 26
        return result
    
    def delete_sheet(self, sheet_id: str) -> bool:
        """
        删除指定的工作表
        
        Args:
            sheet_id: 要删除的sheet ID
            
        Returns:
            是否成功
        """
        if not self.spreadsheet_token:
            return False
            
        self._get_access_token()
        self._rate_limit()
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/{sheet_id}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    print(f"  ✅ 删除默认Sheet")
                    return True
            return False
        except Exception:
            return False
    
    def update_sheet_properties(self, sheet_id: str, new_title: str) -> bool:
        """
        更新工作表属性（如名称）
        
        Args:
            sheet_id: sheet ID
            new_title: 新的标题
            
        Returns:
            是否成功
        """
        if not self.spreadsheet_token:
            return False
            
        self._get_access_token()
        self._rate_limit()
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/{sheet_id}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # 使用正确的格式 - 直接传递title
        data = {
            "title": new_title
        }
        
        try:
            # 使用PATCH方法
            response = requests.patch(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return True
            return False
        except Exception:
            return False
    
    def get_share_url(self) -> str:
        """
        获取分享链接
        
        Returns:
            飞书表格链接
        """
        if self.spreadsheet_token:
            return f"https://ai1rvq4k35h.feishu.cn/sheets/{self.spreadsheet_token}"
        return ""
    
    def set_share_permissions(self, user_emails: list = None) -> bool:
        """
        设置分享权限（尝试添加协作者）
        
        Args:
            user_emails: 用户邮箱列表
            
        Returns:
            是否成功
        """
        if not self.spreadsheet_token:
            return False
        
        if not user_emails:
            print("  ℹ️ 未提供用户邮箱，跳过权限设置")
            print("  💡 提示: 可以手动在飞书中设置分享权限")
            return True
        
        self._get_access_token()
        success_count = 0
        
        for email in user_emails:
            self._rate_limit()
            
            # 尝试通过邮箱添加协作者
            url = f"{self.base_url}/drive/v1/permissions/{self.spreadsheet_token}/members"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "type": "user",
                "member_type": "email", 
                "member_id": email,
                "perm": "edit"
            }
            
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        print(f"  ✅ 添加协作者成功: {email}")
                        success_count += 1
                    else:
                        print(f"  ⚠️ 添加协作者失败 {email}: {result.get('msg')}")
                else:
                    print(f"  ⚠️ 无法添加协作者 {email}")
            except Exception as e:
                print(f"  ⚠️ 权限设置异常: {e}")
        
        return success_count > 0
    
    def upload_all_worksheets(self, worksheets_data: Dict[str, pd.DataFrame]) -> bool:
        """
        批量上传多个工作表
        
        Args:
            worksheets_data: {sheet_name: DataFrame} 字典
            
        Returns:
            是否全部成功
        """
        success_count = 0
        total_count = len(worksheets_data)
        
        print(f"\n📤 开始上传 {total_count} 个工作表到飞书...")
        
        # 首先查询现有的sheets
        if self.spreadsheet_token and not self.default_sheet_id:
            self._query_existing_sheets()
        
        # 标记是否是第一个工作表
        is_first = True
        
        for sheet_name, df in worksheets_data.items():
            if df is not None and not df.empty:
                try:
                    # 如果是第一个工作表且有默认sheet，重命名并使用它
                    if is_first and self.default_sheet_id:
                        # 先重命名默认sheet
                        if self.update_sheet_properties(self.default_sheet_id, sheet_name):
                            print(f"  ✅ 重命名默认Sheet为: {sheet_name}")
                        else:
                            print(f"  ⚠️ 无法重命名默认Sheet，保持Sheet1")
                        
                        # 记录这个映射
                        self.sheet_ids[sheet_name] = self.default_sheet_id
                        
                        # 写入数据
                        if self._write_data_only(sheet_name, df):
                            success_count += 1
                        
                        is_first = False
                    else:
                        # 创建新的工作表并写入数据
                        if self.write_data_to_sheet(sheet_name, df):
                            success_count += 1
                except Exception as e:
                    print(f"    ❌ {sheet_name} 上传失败: {e}")
        
        print(f"\n📊 上传完成: {success_count}/{total_count} 个工作表成功")
        
        # 显示分享链接
        share_url = self.get_share_url()
        if share_url:
            print(f"🔗 飞书表格链接: {share_url}")
            print(f"\n💡 权限设置提示:")
            print(f"   1. 打开上述链接")
            print(f"   2. 点击右上角'分享'按钮")
            print(f"   3. 选择'链接分享'")
            print(f"   4. 设置为'获得链接的人可编辑'")
            print(f"   5. 复制链接分享给需要的人")
        
        return success_count == total_count
    
    def _query_existing_sheets(self):
        """查询现有的sheets信息"""
        if not self.spreadsheet_token:
            return
            
        self._get_access_token()
        self._rate_limit()
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/query"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    sheets = result.get('data', {}).get('sheets', [])
                    if sheets and len(sheets) == 1:  # 只有一个默认sheet
                        self.default_sheet_id = sheets[0].get('sheet_id')
                        print(f"  📝 检测到默认Sheet (ID: {self.default_sheet_id})")
        except Exception:
            pass
    
    def _write_data_only(self, sheet_name: str, df: pd.DataFrame) -> bool:
        """只写入数据，不创建新sheet（用于默认sheet）"""
        if not self.spreadsheet_token:
            return False
            
        sheet_id = self.sheet_ids.get(sheet_name)
        if not sheet_id:
            return False
        
        # 准备数据
        data = self._prepare_data_for_feishu(df)
        
        # 计算范围
        end_col = self._number_to_column(len(df.columns))
        end_row = len(data)
        range_str = f"{sheet_id}!A1:{end_col}{end_row}"
        
        self._get_access_token()
        self._rate_limit()
        
        # 使用v2 API
        url = f"{self.base_url}/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_batch_update"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "valueRanges": [{
                "range": range_str,
                "values": data
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 0:
                print(f"    ✅ 数据写入: {sheet_name} ({len(df)}行 × {len(df.columns)}列)")
                return True
            else:
                print(f"    ❌ 写入失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            print(f"    ❌ 写入数据失败: {e}")
            return False