# 飞书API集成指南 - 核心逻辑

## 🚀 快速开始

### 1. 配置文件 (feishu_config.json)
```json
{
  "app_id": "cli_a81f553fbc3d9013",
  "app_secret": "Ail6n0G2CiJfxqlbmQQQXWB5JuWQOSNx"
}
```

### 2. 运行测试脚本
```bash
/Users/wenxiangxu/opt/anaconda3/envs/crypto_project/bin/python feishu_screener_test.py
```

## 📊 核心API逻辑

### 1. 认证流程
```python
# 获取访问令牌
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
payload = {
    "app_id": app_id,
    "app_secret": app_secret
}
response = requests.post(url, json=payload)
access_token = response.json()["tenant_access_token"]
```

### 2. 创建电子表格
```python
# 创建新表格
url = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets"
headers = {"Authorization": f"Bearer {access_token}"}
data = {"title": "币安代币分析_20250809"}
response = requests.post(url, headers=headers, json=data)
spreadsheet_token = response.json()["spreadsheet"]["spreadsheet_token"]
```

### 3. 创建工作表
```python
# 为每个分析维度创建工作表
url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets"
data = {
    "properties": {
        "title": "原始数据",
        "row_count": 1000,
        "column_count": 26
    }
}
response = requests.post(url, headers=headers, json=data)
sheet_id = response.json()["sheet"]["sheet_id"]
```

### 4. 数据写入
```python
# 批量写入数据（重要：数据类型转换）
def prepare_data_for_feishu(df):
    """准备DataFrame数据用于飞书上传"""
    data_list = []
    
    # 添加表头
    data_list.append(df.columns.tolist())
    
    # 转换数据行（关键：处理布尔值和NaN）
    for _, row in df.iterrows():
        row_data = []
        for val in row.values:
            if isinstance(val, bool):
                row_data.append(str(val))  # 布尔值转字符串
            elif pd.isna(val):
                row_data.append("")  # NaN转空字符串
            else:
                row_data.append(val)
        data_list.append(row_data)
    
    return data_list

# 写入数据
url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/values"
data = {
    "valueRanges": [{
        "range": f"{sheet_id}!A1:Z1000",
        "values": prepare_data_for_feishu(df)
    }]
}
response = requests.put(url, headers=headers, json=data)
```

## 💡 重要注意事项

### 数据类型处理
1. **布尔值必须转换为字符串** - 飞书API不接受布尔类型
2. **NaN值必须转换为空字符串** - 避免JSON序列化错误
3. **大数字格式化为M/B** - 提高可读性

### API限制
- 单次请求最大5000个单元格
- QPS限制：20次/秒
- 建议使用批量操作减少请求次数

### 错误处理
```python
# 常见错误码
# 90204: invalid cell type, type is bool - 布尔值未转换
# 99991: 权限不足 - 检查app权限配置
# 1254043: 表格不存在 - 检查spreadsheet_token
```

## 🎯 完整工作流程

1. **初始化连接**
   - 加载配置文件
   - 获取访问令牌

2. **数据准备**
   - 从币安API获取数据
   - 数据清洗和格式化
   - 类型转换（布尔值、NaN处理）

3. **创建表格结构**
   - 创建主电子表格
   - 为每个分析维度创建工作表

4. **数据上传**
   - 批量写入数据
   - 处理大数据集分批上传

5. **获取分享链接**
   ```python
   share_url = f"https://ai1rvq4k35h.feishu.cn/sheets/{spreadsheet_token}"
   ```

## 📈 测试结果

### 成功案例
- ✅ 创建表格：币安代币分析_20250809_0034
- ✅ 表格Token：EYCEsDjOuhdgIUtMP51ceiXEnFf
- ✅ 成功创建5/5个工作表
- ✅ 总数据量：246行
- ✅ 执行时间：7.04秒

### 分析维度
1. **原始数据** - 62行 × 13列
2. **交易量排行** - 62行 × 14列
3. **市值排行** - 41行 × 14列
4. **涨跌排行** - 35行 × 15列
5. **期货专注** - 46行 × 14列

## 🔧 优化建议

1. **使用连接池** - 复用HTTP连接提高性能
2. **实现重试机制** - 处理临时网络问题
3. **添加进度条** - 显示上传进度
4. **缓存令牌** - 减少认证请求

## 📚 参考资源

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [电子表格API指南](https://open.feishu.cn/document/ukTMukTMukTM/uATMzUjLwEzM14CMxMTN)
- 测试脚本：`feishu_screener_test.py`
- 配置文件：`feishu_config.json`

---
**创建日期**: 2025-08-09
**版本**: 1.0
**状态**: 已测试通过