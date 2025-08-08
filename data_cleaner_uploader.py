#!/usr/bin/env python3
"""
数据清理和Google Sheets上传器
1. 手动删除指定交易对
2. 数据格式化 (M为单位)
3. 持仓量转换为USD价值
4. 上传到Google Sheets
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
from enhanced_token_screener import FinalFixedScreener
from google.oauth2.service_account import Credentials
import gspread

class DataCleanerUploader:
    def __init__(self):
        self.screener = FinalFixedScreener()
        
        # 需要手动删除的交易对
        self.excluded_tokens = {'LINA', 'ALPACA', 'VIDT', 'AGIX', 'FTM', 'BNX'}
        
        # Google Sheets配置
        self.sheet_name = "币安代币筛选数据"
        self.worksheet_name = "最新数据"
        
        # 初始化Google Sheets客户端
        self.gc = None
        self.sheet = None
        
    def setup_google_sheets(self, credentials_file="credentials.json"):
        """设置Google Sheets连接"""
        try:
            # 检查凭证文件是否存在
            if not os.path.exists(credentials_file):
                print(f"❌ 找不到Google凭证文件: {credentials_file}")
                print("请确保已下载Google服务账户凭证文件并重命名为 credentials.json")
                return False
            
            # Google Sheets API权限范围
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 加载凭证
            credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
            self.gc = gspread.authorize(credentials)
            
            print("✅ Google Sheets连接设置成功")
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets设置失败: {e}")
            return False
    
    def create_or_get_sheet(self):
        """创建或获取Google Sheet"""
        try:
            # 尝试打开现有的工作表
            try:
                self.sheet = self.gc.open(self.sheet_name)
                print(f"✅ 找到现有工作表: {self.sheet_name}")
            except gspread.SpreadsheetNotFound:
                # 创建新的工作表
                self.sheet = self.gc.create(self.sheet_name)
                print(f"✅ 创建新工作表: {self.sheet_name}")
            
            # 获取或创建工作页
            try:
                worksheet = self.sheet.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(title=self.worksheet_name, rows=1000, cols=30)
                print(f"✅ 创建新工作页: {self.worksheet_name}")
            
            return worksheet
            
        except Exception as e:
            print(f"❌ 工作表操作失败: {e}")
            return None
    
    def filter_excluded_tokens(self, df):
        """过滤掉指定的交易对"""
        print(f"🗑️ 过滤指定交易对: {self.excluded_tokens}")
        
        initial_count = len(df)
        filtered_df = df[~df['base_asset'].isin(self.excluded_tokens)]
        filtered_count = len(filtered_df)
        
        excluded_count = initial_count - filtered_count
        print(f"📊 过滤结果: 删除 {excluded_count} 个交易对，保留 {filtered_count} 个")
        
        if excluded_count > 0:
            excluded_list = df[df['base_asset'].isin(self.excluded_tokens)]['base_asset'].tolist()
            print(f"已删除的交易对: {excluded_list}")
        
        # 重新排序和编号
        filtered_df = filtered_df.sort_values('total_volume_24h', ascending=False).reset_index(drop=True)
        filtered_df['volume_rank'] = range(1, len(filtered_df) + 1)
        
        return filtered_df
    
    def format_large_numbers(self, value, decimal_places=2):
        """将大数字格式化为M单位"""
        if pd.isna(value) or value == 0:
            return "0"
        
        try:
            value = float(value)
            if value >= 1000000:
                return f"{value / 1000000:.{decimal_places}f}M"
            elif value >= 1000:
                return f"{value / 1000:.{decimal_places}f}K"
            else:
                return f"{value:.{decimal_places}f}"
        except:
            return "0"
    
    def calculate_position_value_in_usd(self, df):
        """计算持仓量的USD价值"""
        print("💰 计算持仓量USD价值...")
        
        # 计算当前持仓量USD价值
        df['open_interest_usd'] = df['open_interest'] * df['price']
        
        # 计算7日平均持仓量USD价值  
        df['avg_7d_oi_usd'] = df['avg_7d_oi'] * df['price']
        
        return df
    
    def clean_and_format_data(self, df):
        """清理和格式化数据"""
        print("🧹 清理和格式化数据...")
        
        # 1. 过滤指定交易对
        df = self.filter_excluded_tokens(df)
        
        # 2. 计算持仓量USD价值
        df = self.calculate_position_value_in_usd(df)
        
        # 3. 创建格式化的DataFrame
        formatted_df = df.copy()
        
        # 格式化大额数据为M单位
        large_value_columns = [
            ('market_cap', '市值'),
            ('fully_diluted_market_cap', '完全稀释市值'),
            ('spot_volume_24h', '24h现货交易量'),
            ('futures_volume_24h', '24h期货交易量'), 
            ('total_volume_24h', '24h总交易量'),
            ('spot_avg_14d_volume', '14日现货平均交易量'),
            ('futures_avg_14d_volume', '14日期货平均交易量'),
            ('open_interest_usd', '当前持仓量USD价值'),
            ('avg_7d_oi_usd', '7日平均持仓量USD价值')
        ]
        
        for col, display_name in large_value_columns:
            if col in formatted_df.columns:
                formatted_df[f'{display_name}(M)'] = formatted_df[col].apply(self.format_large_numbers)
        
        # 格式化小数位数
        percentage_columns = ['1d_return', '3d_return', '7d_return', '14d_return']
        for col in percentage_columns:
            if col in formatted_df.columns:
                formatted_df[f'{col}_formatted'] = formatted_df[col].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) and x != 0 else "0.00%")
        
        # 格式化资金费率
        if 'funding_rate' in formatted_df.columns:
            formatted_df['funding_rate_formatted'] = formatted_df['funding_rate'].apply(lambda x: f"{x:.4f}" if pd.notna(x) and x != 0 else "0.0000")
        
        # 格式化价格
        if 'price' in formatted_df.columns:
            formatted_df['price_formatted'] = formatted_df['price'].apply(lambda x: f"${x:.6f}" if pd.notna(x) and x != 0 else "$0.000000")
        
        return formatted_df
    
    def prepare_sheet_data(self, df):
        """准备上传到Google Sheets的数据"""
        print("📋 准备Google Sheets数据...")
        
        # 选择要上传的列和顺序
        sheet_columns = [
            ('volume_rank', '排名'),
            ('base_asset', '代币'),
            ('price_formatted', '价格(USDT)'),
            ('市值(M)', '市值(M USD)'),
            ('完全稀释市值(M)', '完全稀释市值(M USD)'),
            ('24h现货交易量(M)', '24h现货量(M USDT)'),
            ('24h期货交易量(M)', '24h期货量(M USDT)'),
            ('24h总交易量(M)', '24h总量(M USDT)'),
            ('当前持仓量USD价值(M)', '持仓量(M USD)'),
            ('7日平均持仓量USD价值(M)', '7日平均持仓(M USD)'),
            ('funding_rate_formatted', '资金费率'),
            ('1d_return_formatted', '1日涨跌'),
            ('3d_return_formatted', '3日涨跌'),
            ('7d_return_formatted', '7日涨跌'),
            ('14d_return_formatted', '14日涨跌'),
            ('market_cap_rank', '市值排名'),
            ('is_special_contract', '特殊合约'),
            ('has_spot', '有现货'),
            ('has_futures', '有期货'),
            ('data_source', '数据来源')
        ]
        
        # 创建最终数据
        final_data = []
        
        # 添加表头
        headers = [display_name for _, display_name in sheet_columns]
        final_data.append(headers)
        
        # 添加数据行
        for _, row in df.iterrows():
            data_row = []
            for col_name, _ in sheet_columns:
                if col_name in row and pd.notna(row[col_name]):
                    value = row[col_name]
                    # 处理不同类型的值
                    if isinstance(value, bool):
                        value = "是" if value else "否"
                    elif col_name == 'is_special_contract':
                        value = "1000x" if value else ""
                    elif isinstance(value, (int, float)):
                        # 处理数值，避免科学计数法
                        if pd.isna(value):
                            value = ""
                        elif isinstance(value, float) and value.is_integer():
                            value = str(int(value))
                        else:
                            value = str(value)
                    else:
                        value = str(value)
                    data_row.append(value)
                else:
                    data_row.append("")
            final_data.append(data_row)
        
        print(f"✅ 准备完成: {len(final_data)} 行数据 (包含表头)")
        return final_data
    
    def upload_to_google_sheets(self, data):
        """上传数据到Google Sheets"""
        print("📤 上传数据到Google Sheets...")
        
        try:
            # 获取工作页
            worksheet = self.create_or_get_sheet()
            if not worksheet:
                return False
            
            # 清空现有数据
            worksheet.clear()
            
            # 添加时间戳（使用新的API格式）
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            timestamp_data = [[f"更新时间: {timestamp}"]]
            worksheet.update(values=timestamp_data, range_name='A1')
            
            # 确保数据格式正确
            if not data or len(data) == 0:
                print("❌ 没有数据可上传")
                return False
            
            # 验证数据格式 - 确保所有行都是列表，且所有元素都是字符串
            clean_data = []
            for row in data:
                if isinstance(row, list):
                    # 确保所有元素都转换为字符串，并处理None值
                    clean_row = []
                    for cell in row:
                        if cell is None:
                            clean_row.append("")
                        elif isinstance(cell, (int, float)):
                            # 处理数值，避免科学计数法
                            if isinstance(cell, float) and cell.is_integer():
                                clean_row.append(str(int(cell)))
                            else:
                                clean_row.append(str(cell))
                        else:
                            clean_row.append(str(cell))
                    clean_data.append(clean_row)
                else:
                    print(f"⚠️ 跳过非列表行: {row}")
            
            if not clean_data:
                print("❌ 清理后没有有效数据")
                return False
            
            # 分别上传表头和数据
            print(f"📋 上传表头...")
            if len(clean_data) > 0:
                header_data = [clean_data[0]]  # 表头
                worksheet.update(values=header_data, range_name='A2')
                print(f"✅ 表头上传成功: {len(header_data[0])} 列")
            
            # 上传数据行
            if len(clean_data) > 1:
                print(f"📊 上传数据...")
                data_rows = clean_data[1:]  # 数据行
                worksheet.update(values=data_rows, range_name='A3')
                print(f"✅ 数据上传成功: {len(data_rows)} 行")
            
            print(f"✅ 成功上传 {len(clean_data)} 行数据到Google Sheets")
            print(f"📊 工作表链接: {self.sheet.url}")
            
            return True
            
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            
            # 提供详细的错误分析
            error_str = str(e).lower()
            if 'invalid value' in error_str:
                print(f"💡 数据格式问题解决方案:")
                print("  - 检查数据中是否有特殊字符")
                print("  - 确保所有数据都是字符串格式")
                print("  - 检查是否有None值或空值")
            elif 'quota' in error_str:
                print(f"💡 配额问题解决方案:")
                print("  - API使用配额已用完")
                print("  - 等待一段时间后重试")
            
            return False
    
    def save_backup_csv(self, df, filename_prefix="cleaned_data"):
        """保存备份CSV文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{self.screener.output_dir}/{filename_prefix}_{timestamp}.csv"
        
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 备份CSV已保存: {filename}")
            return filename
        except Exception as e:
            print(f"❌ 保存备份失败: {e}")
            return None
    
    def generate_summary_report(self, df):
        """生成汇总报告"""
        print("\n📊 数据汇总报告:")
        print("=" * 60)
        
        total_count = len(df)
        has_spot = len(df[df['has_spot']])
        has_futures = len(df[df['has_futures']])
        special_contracts = len(df[df['is_special_contract']]) if 'is_special_contract' in df.columns else 0
        
        print(f"总代币数量: {total_count}")
        print(f"有现货数据: {has_spot} ({has_spot/total_count*100:.1f}%)")
        print(f"有期货数据: {has_futures} ({has_futures/total_count*100:.1f}%)")
        print(f"特殊合约: {special_contracts} ({special_contracts/total_count*100:.1f}%)")
        
        # 交易量统计
        total_spot_volume = df['spot_volume_24h'].sum()
        total_futures_volume = df['futures_volume_24h'].sum()
        total_volume = total_spot_volume + total_futures_volume
        
        print(f"\n💰 交易量统计:")
        print(f"24h现货总量: {self.format_large_numbers(total_spot_volume)} USDT")
        print(f"24h期货总量: {self.format_large_numbers(total_futures_volume)} USDT") 
        print(f"24h总交易量: {self.format_large_numbers(total_volume)} USDT")
        
        if total_volume > 0:
            spot_ratio = total_spot_volume / total_volume * 100
            futures_ratio = total_futures_volume / total_volume * 100
            print(f"现货占比: {spot_ratio:.1f}%")
            print(f"期货占比: {futures_ratio:.1f}%")
        
        # 持仓量统计
        if 'open_interest_usd' in df.columns:
            total_oi_usd = df['open_interest_usd'].sum()
            print(f"\n🏦 持仓量统计:")
            print(f"总持仓量价值: {self.format_large_numbers(total_oi_usd)} USD")
        
        # 显示前10名
        print(f"\n🏆 交易量前10名:")
        top10 = df.head(10)
        for i, (_, row) in enumerate(top10.iterrows(), 1):
            total_vol = self.format_large_numbers(row['total_volume_24h'])
            change = f"{row['1d_return']:+.2f}%" if pd.notna(row['1d_return']) else "N/A"
            print(f"  {i:2d}. {row['base_asset']:8} ${total_vol:>10} USDT ({change})")
    
    def run_complete_process(self, use_google_sheets=True):
        """运行完整的数据处理流程"""
        print("🚀 开始数据清理和上传流程")
        print("=" * 80)
        
        # 1. 生成原始数据
        print("📊 生成原始数据...")
        raw_df = self.screener.generate_final_report()
        
        if raw_df is None:
            print("❌ 原始数据生成失败")
            return None
        
        # 2. 清理和格式化数据
        cleaned_df = self.clean_and_format_data(raw_df)
        
        # 3. 保存备份CSV
        backup_file = self.save_backup_csv(cleaned_df)
        
        # 4. 生成汇总报告
        self.generate_summary_report(cleaned_df)
        
        # 5. 上传到Google Sheets (可选)
        if use_google_sheets:
            if self.setup_google_sheets():
                sheet_data = self.prepare_sheet_data(cleaned_df)
                upload_success = self.upload_to_google_sheets(sheet_data)
                
                if upload_success:
                    print(f"\n🎉 数据处理和上传完成!")
                    print(f"📁 本地备份: {backup_file}")
                    print(f"☁️ Google Sheets: {self.sheet.url}")
                else:
                    print(f"\n⚠️ 数据处理完成，但Google Sheets上传失败")
                    print(f"📁 本地备份: {backup_file}")
            else:
                print(f"\n⚠️ Google Sheets连接失败，仅保存本地文件")
                print(f"📁 本地备份: {backup_file}")
        else:
            print(f"\n✅ 数据清理完成 (跳过Google Sheets上传)")
            print(f"📁 本地备份: {backup_file}")
        
        return cleaned_df

def main():
    """主函数"""
    print("🎯 币安代币数据清理和上传工具")
    print("=" * 80)
    
    uploader = DataCleanerUploader()
    
    # 询问是否使用Google Sheets
    use_sheets = input("是否上传到Google Sheets? (y/n, 默认y): ").lower().strip()
    use_google_sheets = use_sheets != 'n'
    
    if use_google_sheets:
        print("\n📝 Google Sheets使用说明:")
        print("1. 需要先在Google Cloud Console创建服务账户")
        print("2. 下载凭证文件并重命名为 'credentials.json'")
        print("3. 确保凭证文件在当前目录下")
        
        if not os.path.exists("credentials.json"):
            print("\n⚠️ 未找到 credentials.json 文件")
            print("将跳过Google Sheets上传，仅保存本地CSV文件")
            use_google_sheets = False
    
    # 运行完整流程
    result = uploader.run_complete_process(use_google_sheets)
    
    if result is not None:
        print(f"\n📈 处理结果: 成功处理 {len(result)} 个代币")
    else:
        print("\n❌ 处理失败")

if __name__ == "__main__":
    main()