#!/usr/bin/env python3
"""
数据补全功能 - 为缺失的代币补充完整数据
Data supplement function - supplement complete data for missing tokens
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta

class DataSupplementer:
    """数据补全器 - 为低量高市值tab补充缺失的代币数据"""
    
    def __init__(self):
        self.spot_base_url = "https://api.binance.com/api/v3"
        self.futures_base_url = "https://fapi.binance.com/fapi/v1"
        self.rate_limit_delay = 0.1  # 100ms延迟
        
    def get_spot_ticker_24hr(self, symbol):
        """获取特定现货交易对的24小时数据"""
        try:
            url = f"{self.spot_base_url}/ticker/24hr"
            params = {'symbol': f"{symbol}USDT"}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  ⚠️ 获取{symbol}现货数据失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ 获取{symbol}现货数据异常: {e}")
            return None
    
    def get_futures_ticker_24hr(self, symbol):
        """获取特定期货交易对的24小时数据"""
        try:
            # 处理特殊符号（如PEPE -> 1000PEPE）
            futures_symbol = symbol
            if symbol in ['PEPE', 'SHIB', 'FLOKI', 'BONK', 'CAT']:
                futures_symbol = f"1000{symbol}"
                
            url = f"{self.futures_base_url}/ticker/24hr"
            params = {'symbol': f"{futures_symbol}USDT"}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                # 如果1000X格式失败，尝试原始符号
                if futures_symbol != symbol:
                    params = {'symbol': f"{symbol}USDT"}
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        return response.json()
                        
                print(f"  ⚠️ 获取{symbol}期货数据失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ 获取{symbol}期货数据异常: {e}")
            return None
    
    def get_historical_klines(self, symbol, interval='1d', limit=14, is_futures=False):
        """获取历史K线数据用于计算7日/14日涨跌"""
        try:
            if is_futures:
                url = f"{self.futures_base_url}/klines"
                # 处理特殊符号
                if symbol in ['PEPE', 'SHIB', 'FLOKI', 'BONK', 'CAT']:
                    symbol = f"1000{symbol}"
            else:
                url = f"{self.spot_base_url}/klines"
                
            params = {
                'symbol': f"{symbol}USDT",
                'interval': interval,
                'limit': limit + 1  # 多获取一天用于计算
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                klines = response.json()
                return klines
            else:
                return None
                
        except Exception as e:
            print(f"  ❌ 获取{symbol}历史数据异常: {e}")
            return None
    
    def calculate_price_changes(self, klines):
        """从K线数据计算价格变化"""
        if not klines or len(klines) < 2:
            return None, None
            
        current_price = float(klines[-1][4])  # 最新收盘价
        
        # 7日涨跌
        change_7d = None
        if len(klines) >= 8:
            price_7d_ago = float(klines[-8][4])
            change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
            
        # 14日涨跌
        change_14d = None
        if len(klines) >= 15:
            price_14d_ago = float(klines[-15][4])
            change_14d = ((current_price - price_14d_ago) / price_14d_ago) * 100
            
        return change_7d, change_14d
    
    def get_funding_rate(self, symbol):
        """获取资金费率"""
        try:
            # 处理特殊符号
            futures_symbol = symbol
            if symbol in ['PEPE', 'SHIB', 'FLOKI', 'BONK', 'CAT']:
                futures_symbol = f"1000{symbol}"
                
            url = f"{self.futures_base_url}/premiumIndex"
            params = {'symbol': f"{futures_symbol}USDT"}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return float(data.get('lastFundingRate', 0)) * 100  # 转换为百分比
            else:
                return 0
        except Exception as e:
            print(f"  ❌ 获取{symbol}资金费率异常: {e}")
            return 0
    
    def supplement_token_data(self, symbol, market_cap_data=None):
        """为单个代币补充完整数据"""
        print(f"  📊 补充{symbol}的数据...")
        
        token_data = {
            'base_asset': symbol,
            'symbol': f"{symbol}USDT",
            'price': 0,
            'spot_volume_24h': 0,
            'futures_volume_24h': 0,
            '1d_return': 0,
            '7d_return': 0,
            '14d_return': 0,
            'funding_rate': 0,
            'market_cap': 0,
            'has_spot': False,
            'has_futures': False,
            'total_volume_24h': 0,
            'spot_volume_14d_avg': 0,
            'futures_volume_14d_avg': 0
        }
        
        # 1. 获取现货数据
        spot_data = self.get_spot_ticker_24hr(symbol)
        if spot_data:
            token_data.update({
                'price': float(spot_data['lastPrice']),
                'spot_volume_24h': float(spot_data['quoteVolume']),
                '1d_return': float(spot_data['priceChangePercent']),
                'has_spot': True
            })
            
            # 获取现货历史数据
            spot_klines = self.get_historical_klines(symbol, limit=14, is_futures=False)
            if spot_klines:
                change_7d, change_14d = self.calculate_price_changes(spot_klines)
                if change_7d is not None:
                    token_data['7d_return'] = change_7d
                if change_14d is not None:
                    token_data['14d_return'] = change_14d
                    
                # 计算14日平均交易量
                volumes = [float(k[7]) for k in spot_klines[:-1]]  # 排除今天
                if volumes:
                    token_data['spot_volume_14d_avg'] = sum(volumes) / len(volumes)
        
        time.sleep(self.rate_limit_delay)
        
        # 2. 获取期货数据
        futures_data = self.get_futures_ticker_24hr(symbol)
        if futures_data:
            token_data.update({
                'futures_volume_24h': float(futures_data['quoteVolume']),
                'has_futures': True
            })
            
            # 如果没有现货价格，使用期货价格
            if token_data['price'] == 0:
                token_data['price'] = float(futures_data['lastPrice'])
                token_data['1d_return'] = float(futures_data['priceChangePercent'])
                
            # 获取期货历史数据（如果现货没有历史数据）
            if token_data['7d_return'] == 0 or token_data['14d_return'] == 0:
                futures_klines = self.get_historical_klines(symbol, limit=14, is_futures=True)
                if futures_klines:
                    change_7d, change_14d = self.calculate_price_changes(futures_klines)
                    if change_7d is not None and token_data['7d_return'] == 0:
                        token_data['7d_return'] = change_7d
                    if change_14d is not None and token_data['14d_return'] == 0:
                        token_data['14d_return'] = change_14d
                        
                    # 计算14日平均期货交易量
                    volumes = [float(k[7]) for k in futures_klines[:-1]]
                    if volumes:
                        token_data['futures_volume_14d_avg'] = sum(volumes) / len(volumes)
            
            # 获取资金费率
            token_data['funding_rate'] = self.get_funding_rate(symbol)
        
        time.sleep(self.rate_limit_delay)
        
        # 3. 使用提供的市值数据
        if market_cap_data and symbol in market_cap_data:
            token_data['market_cap'] = market_cap_data[symbol].get('market_cap', 0)
        
        # 4. 计算总交易量
        token_data['total_volume_24h'] = token_data['spot_volume_24h'] + token_data['futures_volume_24h']
        
        print(f"    ✅ 价格: ${token_data['price']:.6f}, 现货量: ${token_data['spot_volume_24h']/1e6:.1f}M, 期货量: ${token_data['futures_volume_24h']/1e6:.1f}M")
        
        return token_data
    
    def supplement_multiple_tokens(self, symbols, market_cap_data=None):
        """批量补充多个代币的数据"""
        print(f"📊 开始补充{len(symbols)}个代币的数据...")
        
        supplemented_data = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] 处理{symbol}...")
            
            try:
                token_data = self.supplement_token_data(symbol, market_cap_data)
                supplemented_data.append(token_data)
                
                # 每5个代币休息一下，避免触发限制
                if i % 5 == 0:
                    print("  💤 休息1秒避免API限制...")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"  ❌ 处理{symbol}失败: {e}")
                # 添加空数据
                supplemented_data.append({
                    'base_asset': symbol,
                    'symbol': f"{symbol}USDT",
                    'price': 0,
                    'spot_volume_24h': 0,
                    'futures_volume_24h': 0,
                    '1d_return': 0,
                    '7d_return': 0,
                    '14d_return': 0,
                    'funding_rate': 0,
                    'market_cap': market_cap_data.get(symbol, {}).get('market_cap', 0) if market_cap_data else 0,
                    'has_spot': False,
                    'has_futures': False,
                    'total_volume_24h': 0
                })
        
        print(f"\n✅ 完成！成功补充{len(supplemented_data)}个代币的数据")
        return pd.DataFrame(supplemented_data)


# 测试函数
if __name__ == "__main__":
    print("🚀 测试数据补全功能...")
    print("=" * 70)
    
    # 创建补全器
    supplementer = DataSupplementer()
    
    # 测试补充单个代币
    test_symbols = ['RENDER', 'IMX', 'QNT']
    
    print(f"\n测试补充{test_symbols}的数据:")
    
    # 模拟市值数据
    mock_market_cap_data = {
        'RENDER': {'market_cap': 2_100_000_000},
        'IMX': {'market_cap': 1_000_000_000},
        'QNT': {'market_cap': 1_800_000_000}
    }
    
    # 批量补充
    df = supplementer.supplement_multiple_tokens(test_symbols, mock_market_cap_data)
    
    # 显示结果
    print("\n📊 补充的数据:")
    print(df[['base_asset', 'price', 'spot_volume_24h', 'futures_volume_24h', '1d_return', '7d_return', 'market_cap']])