#!/usr/bin/env python3
"""
CoinGecko API Integration for Real Market Cap Data
集成CoinGecko API获取真实市值数据

Free tier limits:
- 10-50 calls/minute (depending on endpoint)
- No API key required for basic endpoints
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta
import pandas as pd

class CoinGeckoClient:
    """CoinGecko API客户端，用于获取真实市值数据"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache_file = "coingecko_market_data_cache.json"
        self.cache_duration_hours = 1  # 缓存1小时
        self.rate_limit_delay = 1.2  # 延迟1.2秒以确保不超过速率限制
        
        # 币安符号到CoinGecko ID的映射
        self.symbol_to_id_map = self._load_symbol_mapping()
        
    def _load_symbol_mapping(self):
        """加载币安符号到CoinGecko ID的映射"""
        # 常见代币的映射
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'USDC': 'usd-coin',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'TRX': 'tron',
            'TON': 'the-open-network',
            'AVAX': 'avalanche-2',
            'SHIB': 'shiba-inu',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'BCH': 'bitcoin-cash',
            'NEAR': 'near',
            'MATIC': 'matic-network',
            'LTC': 'litecoin',
            'ICP': 'internet-computer',
            'DAI': 'dai',
            'UNI': 'uniswap',
            'ETC': 'ethereum-classic',
            'APT': 'aptos',
            'STX': 'stacks',
            'ATOM': 'cosmos',
            'XLM': 'stellar',
            'OKB': 'okb',
            'INJ': 'injective-protocol',
            'FIL': 'filecoin',
            'ARB': 'arbitrum',
            'VET': 'vechain',
            'OP': 'optimism',
            'AAVE': 'aave',
            'MKR': 'maker',
            'SUI': 'sui',
            'GRT': 'the-graph',
            'THETA': 'theta-token',
            'FTM': 'fantom',
            'ALGO': 'algorand',
            'BSV': 'bitcoin-sv',
            'SAND': 'the-sandbox',
            'AXS': 'axie-infinity',
            'EOS': 'eos',
            'MANA': 'decentraland',
            'XTZ': 'tezos',
            'QNT': 'quant-network',
            'FLOW': 'flow',
            'CHZ': 'chiliz',
            'SNX': 'synthetix-network-token',
            'CRV': 'curve-dao-token',
            'GALA': 'gala',
            'PEPE': 'pepe',
            'FLOKI': 'floki',
            'WIF': 'dogwifhat',
            'BONK': 'bonk',
            'POPCAT': 'popcat',
            'BRETT': 'brett',
            'MEW': 'cat-in-a-dogs-world',
            'DOGS': 'dogs-2',
            'PONKE': 'ponke',
            'MINI': 'mini',
            'CAT': 'cat-token',
            # 添加更多映射...
        }
        return mapping
    
    def _load_cache(self):
        """加载缓存的市场数据"""
        if not os.path.exists(self.cache_file):
            return None
            
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(hours=self.cache_duration_hours):
                print("⚠️ CoinGecko缓存已过期")
                return None
                
            print(f"✅ 使用CoinGecko缓存数据 (更新于 {cache_data['timestamp']})")
            return cache_data['data']
            
        except Exception as e:
            print(f"❌ 加载CoinGecko缓存失败: {e}")
            return None
    
    def _save_cache(self, data):
        """保存市场数据到缓存"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
            print("✅ CoinGecko数据已缓存")
        except Exception as e:
            print(f"❌ 保存CoinGecko缓存失败: {e}")
    
    def get_market_data(self, limit=250):
        """
        获取市值排名前N的代币数据
        
        Args:
            limit: 获取数量，最大250（单次请求限制）
            
        Returns:
            包含市值数据的DataFrame
        """
        # 尝试从缓存加载
        cached_data = self._load_cache()
        if cached_data:
            return pd.DataFrame(cached_data)
        
        print(f"🦎 从CoinGecko获取市值前{limit}的代币数据...")
        
        all_data = []
        per_page = 250  # CoinGecko单页最大限制
        pages_needed = (limit + per_page - 1) // per_page
        
        for page in range(1, pages_needed + 1):
            try:
                url = f"{self.base_url}/coins/markets"
                params = {
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': min(per_page, limit - len(all_data)),
                    'page': page,
                    'sparkline': 'false',
                    'price_change_percentage': '24h,7d,14d'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    all_data.extend(data)
                    print(f"  ✅ 获取第{page}页数据，共{len(data)}个代币")
                    
                    # 速率限制
                    if page < pages_needed:
                        time.sleep(self.rate_limit_delay)
                else:
                    print(f"  ❌ 获取第{page}页失败: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"  ❌ 请求CoinGecko API失败: {e}")
                break
        
        if all_data:
            # 保存到缓存
            self._save_cache(all_data)
            
        return pd.DataFrame(all_data)
    
    def get_binance_symbol_market_data(self, binance_symbols):
        """
        获取指定币安符号列表的市值数据
        
        Args:
            binance_symbols: 币安符号列表，如['BTC', 'ETH', 'BNB']
            
        Returns:
            包含市值数据的字典 {symbol: market_data}
        """
        # 首先获取足够多的市场数据
        df = self.get_market_data(250)
        
        if df.empty:
            return {}
        
        # 创建结果字典
        result = {}
        
        # 匹配币安符号
        for symbol in binance_symbols:
            # 尝试直接匹配
            coingecko_id = self.symbol_to_id_map.get(symbol)
            
            if coingecko_id:
                # 在数据中查找
                token_data = df[df['id'] == coingecko_id]
                if not token_data.empty:
                    row = token_data.iloc[0]
                    result[symbol] = {
                        'market_cap': row.get('market_cap', 0),
                        'fully_diluted_valuation': row.get('fully_diluted_valuation', 0),
                        'circulating_supply': row.get('circulating_supply', 0),
                        'total_supply': row.get('total_supply', 0),
                        'max_supply': row.get('max_supply', 0),
                        'price': row.get('current_price', 0),
                        'price_change_24h': row.get('price_change_percentage_24h', 0),
                        'price_change_7d': row.get('price_change_percentage_7d_in_currency', 0),
                        'price_change_14d': row.get('price_change_percentage_14d_in_currency', 0),
                        'market_cap_rank': row.get('market_cap_rank', 0)
                    }
            else:
                # 尝试通过符号匹配
                token_data = df[df['symbol'].str.upper() == symbol.upper()]
                if not token_data.empty:
                    row = token_data.iloc[0]
                    result[symbol] = {
                        'market_cap': row.get('market_cap', 0),
                        'fully_diluted_valuation': row.get('fully_diluted_valuation', 0),
                        'circulating_supply': row.get('circulating_supply', 0),
                        'total_supply': row.get('total_supply', 0),
                        'max_supply': row.get('max_supply', 0),
                        'price': row.get('current_price', 0),
                        'price_change_24h': row.get('price_change_percentage_24h', 0),
                        'price_change_7d': row.get('price_change_percentage_7d_in_currency', 0),
                        'price_change_14d': row.get('price_change_percentage_14d_in_currency', 0),
                        'market_cap_rank': row.get('market_cap_rank', 0)
                    }
        
        return result
    
    def get_top_market_cap_symbols(self, top_n=120):
        """
        获取市值前N的代币符号列表
        
        Returns:
            (symbols, market_data) - 符号列表和完整市场数据
        """
        # 确保获取足够的数据
        fetch_limit = max(top_n, 250)  # 至少获取250个确保覆盖top_n
        df = self.get_market_data(fetch_limit)
        
        if df.empty:
            return [], {}
        
        # 按市值排序并取前N个
        df = df.nlargest(min(top_n, len(df)), 'market_cap')
        
        # 创建币安符号列表和市场数据字典
        symbols = []
        market_data = {}
        
        for _, row in df.iterrows():
            symbol = row['symbol'].upper()
            symbols.append(symbol)
            market_data[symbol] = {
                'market_cap': row.get('market_cap', 0),
                'fully_diluted_valuation': row.get('fully_diluted_valuation', 0),
                'circulating_supply': row.get('circulating_supply', 0),
                'total_supply': row.get('total_supply', 0),
                'price': row.get('current_price', 0),
                'market_cap_rank': row.get('market_cap_rank', 0),
                'coingecko_id': row.get('id', '')
            }
        
        return symbols, market_data


# 测试函数
if __name__ == "__main__":
    print("🚀 测试CoinGecko集成...")
    print("=" * 70)
    
    client = CoinGeckoClient()
    
    # 测试获取市值前10
    print("\n📊 获取市值前10的代币:")
    symbols, market_data = client.get_top_market_cap_symbols(10)
    
    for i, symbol in enumerate(symbols, 1):
        data = market_data[symbol]
        mcap = data['market_cap'] / 1e9  # 转换为十亿
        print(f"{i}. {symbol}: ${mcap:.1f}B (排名#{data['market_cap_rank']})")
    
    # 测试获取特定币安符号的数据
    print("\n📊 测试获取特定代币数据:")
    test_symbols = ['BTC', 'ETH', 'BNB', 'PEPE', 'WIF']
    symbol_data = client.get_binance_symbol_market_data(test_symbols)
    
    for symbol, data in symbol_data.items():
        if data:
            mcap = data['market_cap'] / 1e9
            print(f"{symbol}: 市值=${mcap:.1f}B, 流通量={data['circulating_supply']:,.0f}")