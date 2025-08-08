# CoinGecko集成说明

## 🎯 实现目标
集成CoinGecko免费API获取真实的流通市值数据，替代原有的`交易量×100`的粗略估算方法。

## ✅ 已完成的集成

### 1. CoinGecko客户端模块 (`coingecko_integration.py`)
- **功能**：获取真实市值、流通量、FDV等数据
- **缓存机制**：1小时缓存避免频繁API调用
- **速率限制**：自动延迟1.2秒确保不超限
- **映射表**：币安符号到CoinGecko ID的映射

### 2. 主程序集成
在`binance_token_screener_v1.1.py`中：
- 初始化CoinGecko客户端
- 在`get_enhanced_market_data()`中获取真实市值数据
- 更新所有代币的市值为真实值
- 低量高市值tab使用真实市值前120

### 3. 数据更新逻辑
```python
# 获取真实市值数据
market_cap_data = self.coingecko_client.get_binance_symbol_market_data(all_symbols)

# 更新每个代币的市值
for idx, row in raw_df.iterrows():
    if base_asset in market_cap_data:
        raw_df.loc[idx, 'market_cap'] = coingecko_data['market_cap']
        raw_df.loc[idx, 'circulating_supply'] = coingecko_data['circulating_supply']
```

## 📊 提供的数据

CoinGecko API提供以下真实数据：
- **market_cap**: 流通市值
- **fully_diluted_valuation**: FDV（完全稀释估值）
- **circulating_supply**: 流通供应量
- **total_supply**: 总供应量
- **max_supply**: 最大供应量
- **market_cap_rank**: 市值排名
- **price_change_7d**: 7日涨跌（如果有）
- **price_change_14d**: 14日涨跌（如果有）

## 🔧 使用方式

### 获取市值前N的代币
```python
top_120_symbols, top_120_data = client.get_top_market_cap_symbols(120)
```

### 获取特定代币的市值数据
```python
symbols = ['BTC', 'ETH', 'BNB']
market_data = client.get_binance_symbol_market_data(symbols)
```

## ⚠️ 注意事项

1. **API限制**：免费版每分钟10-50次调用
2. **缓存策略**：数据缓存1小时，避免重复请求
3. **符号映射**：部分代币符号需要映射（如SHIB→shiba-inu）
4. **数据完整性**：不是所有币安代币都在CoinGecko有数据

## 📈 改进效果

### 之前（估算市值）
```python
'market_cap': float(pair['quoteVolume']) * 100  # 非常不准确
```

### 现在（真实市值）
```python
'market_cap': coingecko_data['market_cap']  # 真实流通市值
```

## 🚀 后续优化建议

1. **数据补全**：为市值前120但不在已获取数据中的代币补充数据
2. **批量获取**：优化API调用，一次获取更多数据
3. **错误处理**：增强网络错误和API限制的处理
4. **备用方案**：考虑添加CoinMarketCap作为备用数据源

## 测试结果

✅ 成功获取市值前120的代币数据
✅ 正确更新主程序中的市值数据
✅ 低量高市值tab使用真实市值排序
✅ 缓存机制正常工作

---

**更新日期**: 2025-07-29
**版本**: v1.1