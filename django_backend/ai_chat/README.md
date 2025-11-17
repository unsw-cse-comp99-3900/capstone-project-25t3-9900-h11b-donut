# AI Chat Module

AI对话功能模块，提供智能学习计划解释、任务指导、学习鼓励等功能。

## 功能特性

- 🤖 **智能对话**: 基于用户学习计划数据的个性化AI回复
- 📚 **学习计划解释**: 详细解释AI生成的学习计划原因和结构
- 📝 **任务指导**: 针对具体任务部分提供详细指导
- 💪 **学习鼓励**: 在用户感到困难时提供情感支持
- 📱 **练习建议**: 智能推荐练习内容
- 📅 **7天历史**: 自动存储和管理7天内的对话历史

## 数据模型

### ChatConversation
- 对话会话模型，每个用户一个活跃会话
- 自动管理对话的创建和更新时间

### ChatMessage  
- 聊天消息模型，存储用户和AI的所有消息
- 支持结构化元数据存储

### UserStudyPlan
- 用户学习计划存储，用于AI对话中的计划解释
- 自动标记活跃计划，支持历史版本

## API接口

### POST /api/ai/chat/
发送消息到AI并获取回复
```json
{
  "message": "Please explain my plan for me."
}
```

### GET /api/ai/chat/?limit=50
获取对话历史

### POST /api/ai/study-plan/
保存学习计划数据
```json
{
  "plan_data": { ... }
}
```

### GET /api/ai/study-plan/
获取当前学习计划

### POST /api/ai/cleanup/
清理7天前的旧数据

### GET /api/ai/health/
健康检查

## 部署步骤

1. **添加到Django设置**
   ```python
   # settings.py
   INSTALLED_APPS = [
       # ... 其他应用
       'ai_chat',
   ]
   ```

2. **创建数据库迁移**
   ```bash
   python manage.py makemigrations ai_chat
   python manage.py migrate
   ```

3. **URL配置**
   已自动集成到 `/api/ai/` 路径下

## 前端集成

前端通过 `aiChatService` 与后端API交互：

```typescript
import { aiChatService } from '../services/aiChatService';

// 发送消息
const response = await aiChatService.sendMessage('Hello!');

// 获取历史
const history = await aiChatService.getChatHistory(50);

// 保存学习计划
await aiChatService.saveStudyPlan(planData);
```

## 智能意图识别

AI服务能自动识别以下对话意图：

- **explain_plan**: 学习计划解释请求
- **task_help**: 任务和作业帮助
- **encouragement**: 鼓励和情感支持
- **practice**: 练习和复习建议
- **greeting**: 问候和介绍
- **general**: 通用对话

## 数据清理

系统自动清理7天前的数据：
- 对话记录自动删除
- 旧的学习计划版本清理
- 可通过API手动触发清理

## 安全考虑

- 用户数据隔离：每个用户只能访问自己的对话
- CSRF保护：所有POST请求需要CSRF token
- 登录验证：所有API需要用户登录
- 数据清理：定期清理敏感数据

## 扩展性

模块设计支持轻松扩展：
- 新增对话意图类型
- 自定义AI回复模板
- 集成外部AI服务
- 添加多语言支持