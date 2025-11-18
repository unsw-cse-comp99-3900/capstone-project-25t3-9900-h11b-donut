# AI计划生成问题排查指南

## 问题症状
前端显示："AI计划生成失败: 后端返回空的AI计划数据。请检查网络连接或稍后重试。"

## 诊断结果
经过测试发现：

✅ **后端工作正常**
- AI计划生成API `/api/generate` 成功返回数据
- Gemini API 配置正确，能生成计划
- Token认证机制正常
- z1234567 用户的token有效且未过期

❌ **前端存在问题**
- 前端无法正确处理后端响应

## 解决方案

### 方案1: 更新localStorage中的Token
1. 打开浏览器开发者工具 (F12)
2. 进入 Application/Storage 标签
3. 找到 LocalStorage
4. 将 `auth_token` 更新为:
```
RjiHae_TKoF6di9gfcq7J_HJKcFmj7C1FY3lDQIERCfQc9uePUHAGPmrBwo3kdc8
```

### 方案2: 清除浏览器缓存
1. 清除浏览器缓存和Cookie
2. 重新登录学生账户 (z1234567)
3. 再次尝试生成计划

### 方案3: 检查网络请求
1. 打开开发者工具的Network标签
2. 点击"Generate Plan"按钮
3. 查看对 `/api/generate` 的请求
4. 检查：
   - 请求方法是否为 POST
   - Authorization header是否正确
   - 响应状态码和内容

### 方案4: 手动测试API
在浏览器控制台中运行：
```javascript
fetch('/api/generate', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer RjiHae_TKoF6di9gfcq7J_HJKcFmj7C1FY3lDQIERCfQc9uePUHAGPmrBwo3kdc8',
    'Content-Type': 'application/json'
  }
}).then(r => r.json()).then(console.log)
```

## 技术细节

### 后端响应示例
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "ok": true,
    "relaxation": "none",
    "weekStart": "2025-11-19",
    "days": [...],
    "taskSummary": [...],
    "aiSummary": {
      "tasks": [...]
    }
  }
}
```

### 前端期望的响应
- `res.success` 应该为 `true`
- `res.data` 应该包含有效的计划数据
- `res.data.ok` 应该为 `true`

## 联系信息
如果问题持续存在，请检查：
1. 浏览器控制台是否有JavaScript错误
2. Django服务器日志是否有错误信息
3. 网络连接是否正常