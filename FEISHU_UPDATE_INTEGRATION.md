# 飞书表格固定链接更新功能整合文档
# Feishu Fixed Spreadsheet Update Integration Guide

## 更新概述 / Update Overview
**版本**: v3.1
**日期**: 2025-01-18
**功能**: 每次运行更新同一个飞书表格，而不是创建新表格 / Update same Feishu spreadsheet instead of creating new ones

---

## 核心改动 / Core Changes

### 1. 新增配置文件 / New Configuration File
**文件**: `feishu_spreadsheet_config.json`
```json
{
  "spreadsheet_token": "Mt2usIBNlhBJKHtQS53cykHbnoT",
  "spreadsheet_url": "https://ai1rvq4k35h.feishu.cn/sheets/Mt2usIBNlhBJKHtQS53cykHbnoT",
  "description": "固定的飞书表格，每次运行会更新数据而不是创建新表格"
}
```

### 2. FeishuManager类增强 / FeishuManager Enhancement
**文件**: `feishu_manager.py`

#### 新增方法 / New Methods:
- `open_existing_spreadsheet(spreadsheet_token)` - 打开现有表格
- `_clear_all_sheets()` - 清空所有工作表（保留第一个）
- `upload_all_worksheets(worksheets_data, update_mode=False)` - 支持更新模式

### 3. 主程序智能选择 / Main Program Smart Selection
**文件**: `binance_token_screener_v3.0.py`

#### 逻辑流程 / Logic Flow:
1. 检查是否存在 `feishu_spreadsheet_config.json`
2. 如果存在：
   - 读取固定的 `spreadsheet_token`
   - 打开现有表格
   - 以更新模式上传数据
3. 如果不存在：
   - 创建新表格（传统模式）

---

## 使用指南 / Usage Guide

### 场景1：固定表格模式（推荐）/ Fixed Spreadsheet Mode (Recommended)
```bash
# 确保配置文件存在
ls feishu_spreadsheet_config.json

# 运行程序 - 将更新固定表格
python binance_token_screener_v3.0.py
```

**优点 / Advantages**:
- ✅ 链接永不变化 / Link never changes
- ✅ 历史数据可通过版本历史查看 / Historical data available via version history
- ✅ 便于分享和订阅 / Easy to share and bookmark
- ✅ 自动化友好 / Automation friendly

### 场景2：新建表格模式 / New Spreadsheet Mode
```bash
# 删除或重命名配置文件
mv feishu_spreadsheet_config.json feishu_spreadsheet_config.json.bak

# 运行程序 - 将创建新表格
python binance_token_screener_v3.0.py
```

**适用于 / Suitable for**:
- 需要保留每次运行的独立副本 / Need separate copy for each run
- 测试或调试 / Testing or debugging

---

## 技术细节 / Technical Details

### 更新模式工作流程 / Update Mode Workflow:
1. **打开表格 / Open Spreadsheet**
   ```python
   manager.open_existing_spreadsheet(spreadsheet_token)
   ```

2. **清理现有数据 / Clear Existing Data**
   ```python
   manager._clear_all_sheets()  # 删除除第一个外的所有sheets
   ```

3. **写入新数据 / Write New Data**
   ```python
   manager.upload_all_worksheets(data, update_mode=True)
   ```

### API调用优化 / API Call Optimization:
- 使用批量更新API减少请求次数 / Use batch update API to reduce requests
- 保留第一个sheet避免权限问题 / Keep first sheet to avoid permission issues
- 速率限制: 20 QPS / Rate limit: 20 QPS

---

## 配置管理 / Configuration Management

### 创建新的固定表格 / Create New Fixed Spreadsheet:
```python
# 使用辅助脚本
python create_fixed_feishu_sheet.py

# 或手动创建配置
echo '{
  "spreadsheet_token": "YOUR_TOKEN",
  "spreadsheet_url": "YOUR_URL"
}' > feishu_spreadsheet_config.json
```

### 切换表格 / Switch Spreadsheets:
只需修改 `feishu_spreadsheet_config.json` 中的token即可

---

## 兼容性 / Compatibility

### 向后兼容 / Backward Compatible:
- ✅ 不影响Google Sheets版本 (v2.0)
- ✅ 配置文件不存在时恢复传统行为
- ✅ 所有原有功能保持不变

### 调度器集成 / Scheduler Integration:
```bash
# simple_scheduler.py 无需修改
# 自动使用固定表格（如果配置存在）
./start_simple.sh background
```

---

## 故障排除 / Troubleshooting

### 问题1: 无法打开固定表格
**症状**: "❌ 无法打开现有表格"
**解决**:
1. 检查token是否正确
2. 确认表格未被删除
3. 验证飞书API权限

### 问题2: 工作表清理失败
**症状**: 旧数据仍然存在
**解决**:
1. 手动删除多余的工作表
2. 检查API响应错误
3. 确认token权限

### 问题3: 配置文件未生效
**症状**: 仍在创建新表格
**解决**:
1. 确认文件名正确: `feishu_spreadsheet_config.json`
2. 检查JSON格式是否有效
3. 确认文件在正确目录

---

## 最佳实践 / Best Practices

1. **生产环境** / Production:
   - 使用固定表格模式
   - 定期备份配置文件
   - 监控更新成功率

2. **开发测试** / Development:
   - 使用独立的测试表格
   - 保留配置文件的备份

3. **团队协作** / Team Collaboration:
   - 共享同一个spreadsheet_token
   - 设置适当的权限级别
   - 文档化表格结构

---

## 版本历史 / Version History

### v3.1 (2025-01-18)
- ✅ 添加固定表格更新功能
- ✅ 智能模式选择
- ✅ 向后兼容

### v3.0 (2025-08-30)
- 初始飞书集成
- 创建新表格模式

---

## 相关文件 / Related Files
- `feishu_manager.py` - 飞书API管理器
- `feishu_spreadsheet_config.json` - 固定表格配置
- `test_update_feishu.py` - 更新功能测试脚本
- `binance_token_screener_v3.0.py` - 主程序

---

**维护者** / **Maintainer**: Binance Token Screener Team
**最后更新** / **Last Updated**: 2025-01-18