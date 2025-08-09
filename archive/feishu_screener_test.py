#!/usr/bin/env python3
"""
飞书版本的币安代币筛选器测试
完全使用飞书多维表格代替Google Sheets
参数: 50个现货代币, 50个期货代币
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import logging
import requests

# 导入核心模块
from coingecko_integration import CoinGeckoClient
from data_supplement import DataSupplementer
from feishu_manager import FeishuManager

# 忽略警告
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FeishuBinanceScreener:
    """飞书版币安代币筛选器"""
    
    def __init__(self):
        """初始化筛选器"""
        self.spot_count = 50
        self.futures_count = 50
        self.start_time = datetime.now()
        
        # 创建输出文件夹
        self.output_folder = self.create_output_folder()
        
        # 初始化数据提供者
        self.coingecko_client = CoinGeckoClient()
        self.data_supplementer = DataSupplementer()
        
        # 初始化飞书管理器
        self.feishu_manager = None
        
        # 排除列表
        self.stablecoins = ['USDC', 'FDUSD', 'USD1']
        self.major_coins = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB']
        self.excluded_tokens = ['ALPACA', 'BNX', 'LINA', 'VIDT', 'AGIX', 'FTM']
        
        print("=" * 80)
        print("🚀 飞书版币安代币筛选器 - 测试版本")
        print("=" * 80)
        print(f"📅 运行时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 参数设置: 现货 {self.spot_count} | 期货 {self.futures_count}")
        print("=" * 80)
    
    def create_output_folder(self):
        """创建输出文件夹"""
        date_str = datetime.now().strftime('%Y%m%d')
        folder_name = f"币安代币分析结果_{date_str}"
        
        # 如果是测试运行，添加测试标记
        folder_name = f"飞书测试_{folder_name}"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        # 创建子文件夹
        for subfolder in ['Excel文件', 'CSV文件', '分析报告', '日志文件']:
            subfolder_path = os.path.join(folder_name, subfolder)
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)
        
        print(f"📁 输出文件夹: {folder_name}")
        return folder_name
    
    def init_feishu(self):
        """初始化飞书连接"""
        try:
            print("\n🔐 初始化飞书连接...")
            self.feishu_manager = FeishuManager(config_file='feishu_config.json')
            print("✅ 飞书连接成功")
            return True
        except Exception as e:
            print(f"❌ 飞书连接失败: {e}")
            return False
    
    def fetch_spot_data(self):
        """获取现货数据"""
        print(f"\n📈 获取现货数据 (前{self.spot_count}个)...")
        
        url = "https://api.binance.com/api/v3/ticker/24hr"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 只保留USDT交易对
            df = df[df['symbol'].str.endswith('USDT')]
            
            # 数据类型转换
            numeric_columns = ['lastPrice', 'volume', 'quoteVolume', 'priceChangePercent']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 按24小时交易量排序
            df = df.sort_values('quoteVolume', ascending=False)
            
            # 提取基础资产（去掉USDT后缀）
            df['base_asset'] = df['symbol'].str.replace('USDT$', '', regex=True)
            
            # 获取前N个
            df = df.head(self.spot_count)
            
            print(f"✅ 获取到 {len(df)} 个现货代币")
            return df
            
        except Exception as e:
            print(f"❌ 获取现货数据失败: {e}")
            return pd.DataFrame()
    
    def fetch_futures_data(self):
        """获取期货数据"""
        print(f"\n📊 获取期货数据 (前{self.futures_count}个)...")
        
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 只保留USDT永续合约
            df = df[df['symbol'].str.endswith('USDT')]
            
            # 数据类型转换
            numeric_columns = ['lastPrice', 'volume', 'quoteVolume', 'priceChangePercent']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 按24小时交易量排序
            df = df.sort_values('quoteVolume', ascending=False)
            
            # 提取基础资产（去掉USDT后缀）
            # 注意：期货可能有1000BONK这样的符号，需要标准化
            df['base_asset'] = df['symbol'].str.replace('USDT$', '', regex=True)
            
            # 标准化期货符号（去掉1000前缀）
            df['base_asset'] = df['base_asset'].str.replace('^1000', '', regex=True)
            
            # 获取前N个
            df = df.head(self.futures_count)
            
            print(f"✅ 获取到 {len(df)} 个期货代币")
            return df
            
        except Exception as e:
            print(f"❌ 获取期货数据失败: {e}")
            return pd.DataFrame()
    
    def merge_data(self, spot_df, futures_df):
        """合并现货和期货数据"""
        print("\n🔄 合并数据...")
        
        # 重命名列
        spot_df = spot_df.rename(columns={
            'lastPrice': 'spot_price',
            'quoteVolume': 'spot_volume_24h',
            'priceChangePercent': 'spot_change_24h'
        })
        
        futures_df = futures_df.rename(columns={
            'lastPrice': 'futures_price', 
            'quoteVolume': 'futures_volume_24h',
            'priceChangePercent': 'futures_change_24h'
        })
        
        # 选择需要的列
        spot_cols = ['base_asset', 'spot_price', 'spot_volume_24h', 'spot_change_24h']
        futures_cols = ['base_asset', 'futures_price', 'futures_volume_24h', 'futures_change_24h']
        
        spot_df = spot_df[spot_cols]
        futures_df = futures_df[futures_cols]
        
        # 合并
        merged_df = pd.merge(
            spot_df, 
            futures_df, 
            on='base_asset', 
            how='outer',
            suffixes=('', '_dup')
        )
        
        # 填充缺失值
        merged_df = merged_df.fillna(0)
        
        # 计算总交易量
        merged_df['total_volume_24h'] = merged_df['spot_volume_24h'] + merged_df['futures_volume_24h']
        
        # 添加标记
        merged_df['has_spot'] = merged_df['spot_volume_24h'] > 0
        merged_df['has_futures'] = merged_df['futures_volume_24h'] > 0
        
        print(f"✅ 合并完成，共 {len(merged_df)} 个代币")
        return merged_df
    
    def add_market_cap_data(self, df):
        """添加市值数据"""
        print("\n💰 获取市值数据...")
        
        try:
            # 获取前200个市值代币
            top_symbols, market_cap_data = self.coingecko_client.get_top_market_cap_symbols(200)
            
            # 添加市值数据列
            df['market_cap'] = 0
            df['circulating_supply'] = 0
            df['fdv'] = 0
            
            for _, row in df.iterrows():
                symbol = row['base_asset'].upper()  # 确保大写
                if symbol in market_cap_data:
                    idx = df['base_asset'] == row['base_asset']
                    df.loc[idx, 'market_cap'] = market_cap_data[symbol].get('market_cap', 0)
                    df.loc[idx, 'circulating_supply'] = market_cap_data[symbol].get('circulating_supply', 0)
                    # fdv可能不存在，使用get方法安全获取
                    df.loc[idx, 'fdv'] = market_cap_data[symbol].get('fdv', 0)
            
            print(f"✅ 市值数据添加完成")
            return df
            
        except Exception as e:
            print(f"⚠️ 获取市值数据时出现问题: {e}")
            # 即使出错也返回原始数据框
            if 'market_cap' not in df.columns:
                df['market_cap'] = 0
            if 'circulating_supply' not in df.columns:
                df['circulating_supply'] = 0
            if 'fdv' not in df.columns:
                df['fdv'] = 0
            return df
    
    def format_large_number(self, num):
        """格式化大数字为M/B"""
        if pd.isna(num) or num == 0:
            return "0"
        
        if abs(num) >= 1e9:
            return f"{num/1e9:.2f}B"
        elif abs(num) >= 1e6:
            return f"{num/1e6:.2f}M"
        else:
            return f"{num:.2f}"
    
    def create_analysis_tabs(self, df):
        """创建所有分析标签页"""
        tabs = {}
        
        # 1. 原始数据
        print("\n📊 创建分析标签页...")
        print("  1️⃣ 原始数据")
        raw_df = df.copy()
        raw_df = raw_df[~raw_df['base_asset'].isin(self.stablecoins)]
        tabs['原始数据'] = raw_df
        
        # 2. 交易量排行
        print("  2️⃣ 交易量排行")
        volume_df = df[~df['base_asset'].isin(self.stablecoins)].copy()
        volume_df = volume_df.sort_values('total_volume_24h', ascending=False)
        volume_df['volume_rank'] = range(1, len(volume_df) + 1)
        tabs['交易量排行'] = volume_df
        
        # 3. 市值排行
        print("  3️⃣ 市值排行")
        mcap_df = df[
            (~df['base_asset'].isin(self.stablecoins)) & 
            (~df['base_asset'].isin(self.major_coins)) &
            (df['market_cap'] > 0)
        ].copy()
        mcap_df = mcap_df.sort_values('market_cap', ascending=False)
        mcap_df['mcap_rank'] = range(1, len(mcap_df) + 1)
        tabs['市值排行'] = mcap_df
        
        # 4. 涨跌排行
        print("  4️⃣ 涨跌排行")
        change_df = df[
            (~df['base_asset'].isin(self.stablecoins)) &
            (~df['base_asset'].isin(self.major_coins))
        ].copy()
        
        # 计算1日收益率
        change_df['1d_return'] = change_df['spot_change_24h']
        
        # 涨幅榜
        gainers = change_df[change_df['1d_return'] > 0].nlargest(30, '1d_return')
        gainers['gain_loss_type'] = '涨幅'
        
        # 跌幅榜
        losers = change_df[change_df['1d_return'] < 0].nsmallest(30, '1d_return')
        losers['gain_loss_type'] = '跌幅'
        
        gain_loss_df = pd.concat([gainers, losers])
        tabs['涨跌排行'] = gain_loss_df
        
        # 5. 期货专注
        print("  5️⃣ 期货专注")
        futures_df = df[
            (df['has_futures']) &
            (~df['base_asset'].isin(self.stablecoins)) &
            (~df['base_asset'].isin(self.major_coins))
        ].copy()
        futures_df = futures_df.sort_values('futures_volume_24h', ascending=False)
        futures_df['futures_rank'] = range(1, len(futures_df) + 1)
        tabs['期货专注'] = futures_df
        
        print(f"✅ 创建了 {len(tabs)} 个分析标签页")
        return tabs
    
    def upload_to_feishu(self, tabs):
        """上传数据到飞书"""
        if not self.feishu_manager:
            print("⚠️ 飞书未初始化，跳过上传")
            return False
        
        try:
            print("\n📤 上传数据到飞书...")
            
            # 生成表格名称
            sheet_name = f"币安代币分析_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            # 准备数据：将DataFrame转换为列表格式
            worksheets_data = {}
            for tab_name, df in tabs.items():
                # 格式化数据
                formatted_df = df.copy()
                
                # 格式化大数字列
                for col in ['spot_volume_24h', 'futures_volume_24h', 'total_volume_24h', 'market_cap', 'fdv']:
                    if col in formatted_df.columns:
                        formatted_df[col] = formatted_df[col].apply(self.format_large_number)
                
                # 将布尔值转换为字符串
                for col in formatted_df.columns:
                    if formatted_df[col].dtype == bool:
                        formatted_df[col] = formatted_df[col].astype(str)
                
                # 转换为列表格式（包含表头）
                data_list = [formatted_df.columns.tolist()]  # 表头
                
                # 转换数据行，确保没有布尔值
                for _, row in formatted_df.iterrows():
                    row_data = []
                    for val in row.values:
                        if isinstance(val, bool):
                            row_data.append(str(val))
                        elif pd.isna(val):
                            row_data.append("")
                        else:
                            row_data.append(val)
                    data_list.append(row_data)
                
                worksheets_data[tab_name] = data_list
            
            # 使用专门的加密货币分析表格创建方法
            result = self.feishu_manager.create_crypto_analysis_spreadsheet(
                title=sheet_name,
                worksheets_data=worksheets_data
            )
            
            if result and result.get('spreadsheet_token'):
                spreadsheet_token = result['spreadsheet_token']
                print(f"✅ 创建飞书表格: {sheet_name}")
                print(f"📎 表格Token: {spreadsheet_token}")
                
                # 显示URL
                if result.get('url'):
                    print(f"\n🔗 飞书表格链接: {result['url']}")
                
                # 显示统计信息
                if result.get('success_count'):
                    print(f"📊 成功创建 {result['success_count']}/{result['total_count']} 个工作表")
                    print(f"📝 总数据量: {result.get('total_rows', 0)} 行")
                
                return True
            else:
                print("❌ 创建飞书表格失败")
                return False
            
        except Exception as e:
            print(f"❌ 上传到飞书失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_local_files(self, tabs):
        """保存本地文件"""
        print("\n💾 保存本地文件...")
        
        # 保存Excel文件
        excel_path = os.path.join(
            self.output_folder, 
            'Excel文件',
            f"币安代币分析_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for tab_name, df in tabs.items():
                    df.to_excel(writer, sheet_name=tab_name, index=False)
            print(f"✅ Excel文件保存: {excel_path}")
        except Exception as e:
            print(f"❌ Excel保存失败: {e}")
            
            # 备份为CSV
            for tab_name, df in tabs.items():
                csv_path = os.path.join(
                    self.output_folder,
                    'CSV文件',
                    f"{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                )
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print("✅ 已保存为CSV文件备份")
    
    def run(self):
        """运行筛选器"""
        try:
            # 初始化飞书
            if not self.init_feishu():
                print("⚠️ 飞书初始化失败，将只保存本地文件")
            
            # 获取数据
            spot_df = self.fetch_spot_data()
            futures_df = self.fetch_futures_data()
            
            if spot_df.empty and futures_df.empty:
                print("❌ 无法获取数据，退出")
                return
            
            # 合并数据
            merged_df = self.merge_data(spot_df, futures_df)
            
            # 添加市值数据
            merged_df = self.add_market_cap_data(merged_df)
            
            # 创建分析标签页
            tabs = self.create_analysis_tabs(merged_df)
            
            # 保存本地文件
            self.save_local_files(tabs)
            
            # 上传到飞书
            if self.feishu_manager:
                self.upload_to_feishu(tabs)
            
            # 完成
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            print("\n" + "=" * 80)
            print("✅ 分析完成!")
            print(f"⏱️ 总耗时: {duration:.2f} 秒")
            print(f"📁 输出文件夹: {self.output_folder}")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 运行失败: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    screener = FeishuBinanceScreener()
    screener.run()

if __name__ == "__main__":
    main()