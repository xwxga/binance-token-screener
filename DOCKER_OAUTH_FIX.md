# Docker 环境 OAuth 权限范围问题修复指南

## 问题描述

在 Docker 环境中运行时，出现以下错误：

```
❌ 保存到 Google Sheets 失败：Failed to append row: <HttpError 403 when requesting 
https://sheets.googleapis.com/v4/spreadsheets/.../values/Memos%21A%3AZ:append?...
returned "Request had insufficient authentication scopes.". 
Details: "[{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 
'reason': 'ACCESS_TOKEN_SCOPE_INSUFFICIENT', ...}]"
```

## 问题原因

这个错误的原因是 **OAuth token 的权限范围（scopes）不足**。具体原因包括：

1. **Token 文件来源问题**：
   - Docker 环境中的 `token.json` 可能是从另一个环境复制的
   - 原始环境的 OAuth 授权没有包含所有必需的权限范围

2. **权限范围不匹配**：
   - 代码要求以下权限范围：
     - `https://www.googleapis.com/auth/spreadsheets` - Google Sheets API
     - `https://www.googleapis.com/auth/drive.file` - Google Drive API（用于创建/访问文件）
   - 但 `token.json` 中的权限范围可能不完整

3. **授权流程问题**：
   - 在 OAuth 授权时，如果没有强制显示同意屏幕（`prompt='consent'`），可能不会获取所有权限
   - 如果之前已经授权过，Google 可能不会再次请求所有权限

## 解决方案

### 方法 1：使用诊断脚本（推荐）

1. **检查当前 token 的权限范围**：
```bash
python diagnose_oauth_scopes.py
```

2. **如果发现权限不足，脚本会自动提示修复**

### 方法 2：手动重新授权

#### 步骤 1：删除旧 token（在 Docker 容器中）

```bash
# 进入 Docker 容器
docker exec -it <container_name> bash

# 备份旧 token（可选）
cp token.json token.json.backup

# 删除旧 token
rm token.json
```

#### 步骤 2：重新授权

**选项 A：在 Docker 容器中直接授权**（需要端口映射）

```bash
# 确保 Docker 容器映射了端口 8080
docker run -p 8080:8080 ...

# 在容器中运行
python oauth_setup_enhanced.py
# 或
python fix_oauth_token.py
```

**选项 B：在本地机器上授权后复制到 Docker**（推荐）

1. 在本地机器上运行：
```bash
python oauth_setup_enhanced.py
```

2. 将生成的 `token.json` 复制到 Docker 容器：
```bash
docker cp token.json <container_name>:/path/to/project/token.json
```

#### 步骤 3：验证权限范围

```bash
python diagnose_oauth_scopes.py
```

应该看到所有必需的权限范围都已包含。

### 方法 3：使用修复脚本

```bash
python fix_oauth_token.py
```

这个脚本会：
- 自动删除旧 token
- 启动新的授权流程
- 确保获取所有必需的权限范围

## 验证修复

运行诊断脚本验证：

```bash
python diagnose_oauth_scopes.py
```

应该看到：
```
✅ 所有必需的权限范围都已包含
```

## Docker 环境特殊注意事项

### 1. 端口映射

如果要在 Docker 容器中直接授权，需要确保端口映射正确：

```bash
docker run -p 8080:8080 ...
```

### 2. 浏览器访问

在 Docker 环境中，`run_local_server` 可能无法自动打开浏览器。可以：

1. **手动访问授权 URL**：
   - 脚本会显示授权 URL
   - 在本地浏览器中访问该 URL
   - 完成授权后，将授权码复制回终端

2. **使用本地授权**：
   - 在本地机器上运行授权脚本
   - 将生成的 `token.json` 复制到 Docker 容器

### 3. 网络问题

如果 Docker 容器无法访问 Google OAuth 服务器：

1. 检查网络连接
2. 检查代理设置（如果有）
3. 使用本地授权后复制 token

## 预防措施

1. **首次授权时确保包含所有权限**：
   - 使用 `oauth_setup_enhanced.py` 脚本
   - 确保在授权时选择所有请求的权限

2. **定期检查 token 状态**：
   - 运行 `diagnose_oauth_scopes.py` 检查权限范围
   - 如果 token 过期，会自动刷新（如果有 refresh_token）

3. **备份 token 文件**：
   - 在 Docker 部署前，确保 token.json 包含所有必需的权限范围
   - 定期备份 token.json 文件

## 相关文件

- `diagnose_oauth_scopes.py` - 诊断和修复脚本
- `fix_oauth_token.py` - OAuth token 修复脚本
- `oauth_setup_enhanced.py` - 增强版 OAuth 设置脚本
- `token.json` - OAuth 访问令牌（包含权限范围信息）
- `oauth_credentials.json` - OAuth 客户端凭据

## 常见问题

### Q: 为什么会出现权限范围不足？

A: 通常是因为：
1. Token 是从另一个环境复制的，但原始授权不完整
2. 授权时没有强制显示同意屏幕
3. Google 账户中已经授权过，但没有包含所有权限

### Q: 如何检查 token 中的权限范围？

A: 运行诊断脚本：
```bash
python diagnose_oauth_scopes.py
```

或者直接查看 `token.json` 文件中的 `scopes` 字段。

### Q: 修复后还是不行怎么办？

A: 
1. 检查 `oauth_credentials.json` 是否正确
2. 在 Google Cloud Console 中检查 API 是否已启用
3. 尝试撤销授权后重新授权：
   - 访问：https://myaccount.google.com/permissions
   - 找到并撤销应用授权
   - 重新运行授权脚本

### Q: Docker 容器中无法打开浏览器怎么办？

A: 使用本地授权方法：
1. 在本地机器上运行授权脚本
2. 将生成的 `token.json` 复制到 Docker 容器

## 总结

Docker 环境中的 OAuth 权限范围问题通常是因为 token 文件中的 scopes 不完整。解决方法：

1. ✅ 使用 `diagnose_oauth_scopes.py` 检查问题
2. ✅ 重新授权获取完整的权限范围
3. ✅ 验证修复是否成功

如果问题持续，请检查：
- OAuth 凭据文件是否正确
- Google Cloud Console 中的 API 是否已启用
- 网络连接是否正常


