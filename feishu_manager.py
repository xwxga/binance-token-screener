#!/usr/bin/env python3
"""
飞书电子表格管理器 - 简化版
用于币安代币筛选器v3.0的飞书表格集成
根据feishu_api_guide.md实现核心功能
"""

import json
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Any
import requests
from requests.exceptions import (
    RequestException,
    ConnectionError as RequestsConnectionError,
    Timeout,
    SSLError,
)

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
        self.session = requests.Session()
        
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

    def _request(self, method: str, url: str, retries: int = 3, retry_backoff: float = 1.0, **kwargs) -> requests.Response:
        """
        封装requests请求，带自动重试，处理网络抖动
        """
        last_exception = None
        for attempt in range(1, retries + 1):
            self._rate_limit()
            try:
                kwargs.setdefault("timeout", 15)
                response = self.session.request(method=method, url=url, **kwargs)
                response.raise_for_status()
                return response
            except (RequestsConnectionError, Timeout, SSLError) as e:
                last_exception = e
                if attempt < retries:
                    wait_seconds = retry_backoff * (2 ** (attempt - 1))
                    print(f"    ⚠️ 网络异常({e.__class__.__name__})，{wait_seconds:.1f}s后重试 ({attempt}/{retries})")
                    time.sleep(wait_seconds)
                    continue
                raise
            except RequestException as e:
                raise
        if last_exception:
            raise last_exception
    
    def _get_access_token(self):
        """获取访问令牌"""
        current_time = time.time()
        
        # 如果token还有效，直接返回
        if self.access_token and current_time < self.token_expires_at:
            return self.access_token
        
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
            response = self._request("post", url, headers=headers, json=payload, retries=3)
        except RequestException as e:
            raise Exception(f"获取访问令牌失败: {e}")
        
        result = response.json()
        
        if result.get("code") == 0:
            self.access_token = result.get("tenant_access_token")
            expire = result.get("expire", 7200)
            self.token_expires_at = current_time + expire - 300  # 提前5分钟刷新
            print("✅ 飞书访问令牌获取成功")
            return self.access_token
        else:
            raise Exception(f"获取token失败: {result.get('msg')}")
    
    def update_spreadsheet_permission(self, spreadsheet_token: str = None) -> bool:
        """
        更新电子表格权限，设置为"任何有链接的人可查看或编辑"
        
        Args:
            spreadsheet_token: 表格token（可选，默认使用当前表格）
            
        Returns:
            是否成功更新权限
        """
        token = spreadsheet_token or self.spreadsheet_token
        if not token:
            print("❌ 没有可用的表格token")
            return False
            
        self._get_access_token()
        
        # 使用drive API更新权限 - type必须作为查询参数
        url = f"{self.base_url}/drive/v1/permissions/{token}/public"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # type作为查询参数（文档类型：sheet表示电子表格）
        params = {"type": "sheet"}
        
        # body中包含权限设置
        data = {
            "link_share_entity": "anyone_editable",  # 任何人可编辑
            "external_access_entity": "open",  # 开放外部访问（可选）
            "security_entity": "anyone_can_edit"  # 任何人可编辑（可选）
        }
        
        try:
            response = self._request("patch", url, headers=headers, params=params, json=data)
        except RequestException as e:
            print(f"⚠️ 更新权限时出错: {e}")
            return False
        
        try:
            result = response.json()
        except ValueError:
            print("⚠️ 无法解析权限设置响应")
            return False
        
        if result.get('code') == 0:
            print(f"✅ 成功设置表格权限: 任何有链接的人可编辑")
            return True
        else:
            print(f"⚠️ 设置权限失败: {result.get('msg', 'Unknown error')}")
            return False
    
    def create_spreadsheet(self, title: str) -> str:
        """
        创建新的电子表格
        
        Args:
            title: 表格标题
            
        Returns:
            spreadsheet_token
        """
        self._get_access_token()
        
        url = f"{self.base_url}/sheets/v3/spreadsheets"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"title": title}
        
        try:
            response = self._request("post", url, headers=headers, json=data)
        except RequestException as e:
            raise Exception(f"创建电子表格失败: {e}")
        
        try:
            result = response.json()
        except ValueError:
            raise Exception("创建电子表格失败: 无法解析飞书响应")
        
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
            
            # 自动更新权限为任何有链接的人可编辑
            self.update_spreadsheet_permission(self.spreadsheet_token)
            
            return self.spreadsheet_token
        else:
            raise Exception(f"创建表格失败: {result.get('msg')}")
    
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
            response = self._request("post", url, headers=headers, json=data)
        except RequestException as e:
            raise Exception(f"创建工作表 {sheet_name} 失败: {e}")
        
        try:
            result = response.json()
        except ValueError:
            raise Exception(f"创建工作表失败: 无法解析飞书响应 ({sheet_name})")
        
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
            response = self._request("post", url, headers=headers, json=payload, retries=4, retry_backoff=1.5)
        except RequestException as e:
            print(f"    ❌ 写入数据失败: {e}")
            return False
        
        try:
            result = response.json()
        except ValueError:
            print("    ❌ 写入失败: 无法解析飞书响应")
            return False
        
        if result.get("code") == 0:
            print(f"    ✅ 数据写入: {sheet_name} ({len(df)}行 × {len(df.columns)}列)")
            return True
        else:
            print(f"    ❌ 写入失败: {result.get('msg')}")
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
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/{sheet_id}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self._request("delete", url, headers=headers)
        except RequestException:
            return False
        
        try:
            result = response.json()
        except ValueError:
            return False
        
        if result.get("code") == 0:
            print(f"  ✅ 删除默认Sheet")
            return True
        return False
    
    def update_sheet_properties(self, sheet_id: str, new_title: str, retries: int = 3) -> bool:
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
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/{sheet_id}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"title": new_title}
        
        for attempt in range(1, retries + 1):
            try:
                response = self._request("patch", url, headers=headers, json=data)
            except RequestException as e:
                print(f"    ⚠️ 重命名工作表异常({attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(0.8 * attempt)
                continue
            
            try:
                result = response.json()
            except ValueError:
                print("    ⚠️ 重命名工作表失败: 无法解析飞书响应")
                return False
            
            if result.get("code") == 0:
                return True
            
            print(f"    ⚠️ 重命名工作表失败({attempt}/{retries}): {result.get('msg', '未知错误')}")
            if attempt < retries:
                time.sleep(0.8 * attempt)
        
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
    
    def upload_all_worksheets(self, worksheets_data: Dict[str, pd.DataFrame], update_mode: bool = False) -> bool:
        """
        批量上传多个工作表

        Args:
            worksheets_data: {sheet_name: DataFrame} 字典
            update_mode: 是否为更新模式（清空现有数据后重写）

        Returns:
            是否全部成功
        """
        success_count = 0
        total_count = len(worksheets_data)

        if update_mode:
            print(f"\n🔄 更新模式: 清空并重新写入 {total_count} 个工作表到飞书...")
            # 更新模式下，先删除所有现有的sheets（除了第一个），然后重新创建
            self._clear_all_sheets()
        else:
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
            if not update_mode:
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
        
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/query"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self._request("get", url, headers=headers)
        except RequestException:
            return
        
        try:
            result = response.json()
        except ValueError:
            pass
        else:
            if result.get('code') == 0:
                sheets = result.get('data', {}).get('sheets', [])
                if sheets:
                    # 如果首次初始化，记录默认Sheet
                    if not self.default_sheet_id:
                        self.default_sheet_id = sheets[0].get('sheet_id')
                        if self.default_sheet_id:
                            print(f"  📝 检测到默认Sheet (ID: {self.default_sheet_id})")
                    
                    # 重置并记录已存在的sheet映射
                    self.sheet_ids.clear()
                    for sheet in sheets:
                        sheet_id = sheet.get('sheet_id')
                        title = sheet.get('title')
                        if sheet_id and title:
                            self.sheet_ids[title] = sheet_id
    
    def open_existing_spreadsheet(self, spreadsheet_token: str) -> bool:
        """
        打开现有的飞书表格

        Args:
            spreadsheet_token: 表格token

        Returns:
            是否成功打开
        """
        self.spreadsheet_token = spreadsheet_token

        # 验证表格是否存在
        self._get_access_token()
        self._rate_limit()

        url = f"{self.base_url}/sheets/v3/spreadsheets/{spreadsheet_token}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    spreadsheet = result.get('data', {}).get('spreadsheet', {})
                    title = spreadsheet.get('title', '未知')
                    print(f"✅ 成功打开现有表格: {title}")
                    print(f"📎 表格Token: {spreadsheet_token}")

                    # 查询现有sheets
                    self._query_existing_sheets()
                    return True
                else:
                    print(f"❌ 无法打开表格: {result.get('msg')}")
                    return False
            else:
                print(f"❌ 表格不存在或无权限访问")
                return False
        except Exception as e:
            print(f"❌ 打开表格失败: {e}")
            return False

    def _clear_all_sheets(self) -> None:
        """
        清空所有工作表（删除除第一个外的所有sheet）
        """
        if not self.spreadsheet_token:
            return

        # 查询所有现有的sheets
        self._get_access_token()
    
        url = f"{self.base_url}/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/query"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
        try:
            response = self._request("get", url, headers=headers)
        except RequestException as e:
            print(f"⚠️ 清空工作表时出错: {e}")
            return
        
        try:
            result = response.json()
        except ValueError:
            print("⚠️ 清空工作表时出错: 飞书响应无法解析")
            return
        
        if result.get('code') == 0:
            sheets = result.get('data', {}).get('sheets', [])

            # 保留第一个sheet，删除其他所有sheets
            if len(sheets) > 0:
                self.default_sheet_id = sheets[0].get('sheet_id')
                self.sheet_ids.clear()

                # 删除其他sheets
                for i in range(1, len(sheets)):
                    sheet_id = sheets[i].get('sheet_id')
                    sheet_title = sheets[i].get('title', f'Sheet{i+1}')
                    if self.delete_sheet(sheet_id):
                        print(f"  ✅ 删除工作表: {sheet_title}")
                    else:
                        print(f"  ⚠️ 无法删除工作表: {sheet_title}")

            print(f"  📝 保留默认Sheet准备更新")
        else:
            print(f"⚠️ 清空工作表时出错: {result.get('msg', '未知错误')}")

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
            response = self._request("post", url, headers=headers, json=payload, retries=4, retry_backoff=1.5)
        except RequestException as e:
            print(f"    ❌ 写入数据失败: {e}")
            return False
        
        try:
            result = response.json()
        except ValueError:
            print("    ❌ 写入失败: 无法解析飞书响应")
            return False
        
        if result.get("code") == 0:
            print(f"    ✅ 数据写入: {sheet_name} ({len(df)}行 × {len(df.columns)}列)")
            return True
        else:
            print(f"    ❌ 写入失败: {result.get('msg')}")
            return False
