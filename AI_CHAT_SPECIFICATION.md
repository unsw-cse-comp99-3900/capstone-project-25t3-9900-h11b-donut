# AI Chat 三模块设计规范

## 总体目标

一个聊天界面，内部包含三种清晰分离的模式：
1. **general_chat** - 日常交流、鼓励、通用学习建议
2. **study_plan_qna** - 回答关于学生存储学习计划的问题
3. **practice_setup** - 生成练习题并开始测验的确定性流程

---

## 1. 共享数据与端点（实际代码中的实现）

### 学习计划存储
- **端点**: `GET /api/ai/study-plan/`
- **方法**: `StudyPlanView.get()`
- **返回**: 当前学习计划数据，包含任务、日期、原因等
- **数据结构**: 
  ```json
  {
    "success": true,
    "plan": {
      "tasks": [
        {
          "day": "Monday",
          "task_name": "Task 1",
          "description": "...",
          "reason": "..."
        }
      ]
    }
  }
  ```

### 题库管理
- **端点**: `GET /api/courses/<course_code>/materials` (课程材料)
- **端点**: `GET /api/courses/<course_code>/tasks` (课程任务)
- **AI生成题目**: `POST /api/ai-question-generator/questions/generate`
- **获取会话题目**: `GET /api/ai-question-generator/questions/session/<session_id>`

### 练习生成
- **端点**: `POST /api/ai/generate-practice/`
- **方法**: `GeneratePracticeView.post()`
- **请求体**: `{ userId, courseId, topicId, numQuestions }`
- **返回**: `{ sessionId, numQuestions }`

---

## 2. mode = "general_chat"

### 触发条件
- 用户打开聊天时的默认模式
- 不涉及学习计划或练习的通用对话

### 行为规范
- 使用友好的欢迎消息
- AI可以自由回答，提供技巧、谈论感受等
- **不应该**：
  - 获取学习计划
  - 开始练习流程

### 当前实现状态
✅ 已实现基本欢迎消息和通用对话功能

---

## 3. mode = "study_plan_qna"

### 进入条件
用户明确询问学习计划时：
- "我这周的计划是什么？"
- "为什么周三有这个任务？"
- "任务3的目标是什么？"
- 或点击"询问我的学习计划"按钮

### 处理流程
1. 调用 `GET /api/ai/study-plan/` 获取存储的计划
2. 将用户问题匹配到：
   - 特定日期/周，或
   - 特定任务ID/标签
3. 两层回复：
   - **第1层**：显示相关计划片段（任务名称、日期、描述、存储的"原因"）
   - **第2层**：可选扩展（使用AI阅读任务的PDF/额外信息提供详细解释，或建议如何调整）

### 重要约束
- 在此模式下，助手应专注于解释计划
- 只有当用户明确要求"做一些练习/测验"时才切换到practice_setup

### 当前实现状态
✅ 已实现学习计划获取和基本解释功能
🔲 需要改进意图识别和模式切换逻辑

---

## 4. mode = "practice_setup"

### 进入条件
用户说：
- "我想练习我的薄弱知识点"
- "我想要一个测验"
- 或点击"生成练习"按钮

### 状态机流程
- **步骤1**: 询问课程（如果缺失）→ 根据学生课程列表验证
- **步骤2**: 询问主题（如果缺失）→ 根据题库的主题列表验证
- **步骤3**: 一旦{课程, 主题}有效：
  - 发送"正在生成你的练习..."消息
  - 调用 `POST /api/ai/generate-practice/` 传入{userId, courseId, topicId}
  - 返回后，发送可点击的按钮：
    - 标签："开始练习会话"
    - onClick：打开 `/practice-session/{sessionId}`

### 重要约束
- 在practice_setup内部，不应回退到通用教练提示
- 应保持严格和确定性，直到练习会话创建并开始

### 当前实现状态
✅ 已实现基本的练习生成流程
✅ 已实现两步UX（生成中→准备就绪）
🔲 需要改进状态管理和错误处理

---

## 5. 意图路由器（伪代码实现）

```typescript
interface ChatState {
  mode: 'general_chat' | 'study_plan_qna' | 'practice_setup';
  practiceState?: {
    course?: string;
    topic?: string;
    stage: 'ask_course' | 'ask_topic' | 'generating' | 'ready';
  };
}

function handleUserMessage(message: string, state: ChatState): ChatResponse {
  // 如果正在练习设置流程中，保持在该模式
  if (state.mode === "practice_setup") {
    return handlePracticeSetup(message, state);
  }
  
  // 如果正在学习计划问答模式
  if (state.mode === "study_plan_qna") {
    // 检查是否明显切换到练习意图
    if (looksLikePracticeIntent(message)) {
      state.mode = "practice_setup";
      return startPracticeFlow(message, state);
    }
    return handleStudyPlanQnA(message, state);
  }

  // 默认：通用聊天
  if (looksLikePracticeIntent(message)) {
    state.mode = "practice_setup";
    return startPracticeFlow(message, state);
  }
  
  if (looksLikeStudyPlanIntent(message)) {
    state.mode = "study_plan_qna";
    return handleStudyPlanQnA(message, state);
  }
  
  return handleGeneralChat(message, state);
}

// 意图识别函数
function looksLikePracticeIntent(message: string): boolean {
  const practiceKeywords = [
    'practice', 'quiz', 'test', 'exercise', 'question', 'weak topic',
    '练习', '测验', '考试', '题目'
  ];
  return practiceKeywords.some(keyword => 
    message.toLowerCase().includes(keyword)
  );
}

function looksLikeStudyPlanIntent(message: string): boolean {
  const planKeywords = [
    'plan', 'schedule', 'task', 'assignment', 'deadline', 'week',
    '计划', '安排', '任务', '作业', '截止日期'
  ];
  return planKeywords.some(keyword => 
    message.toLowerCase().includes(keyword)
  );
}
```

---

## 6. 实现优先级

### 第一阶段：确认API规范
- ✅ 已确认现有端点
- ✅ 已了解数据结构
- 📝 需要完善文档

### 第二阶段：实现模式处理器
1. **practice_setup** - 已基本完成，需要优化
2. **study_plan_qna** - 已基本完成，需要改进意图识别
3. **general_chat** - 已完成

### 第三阶段：集成意图路由器
- 在ChatWindow组件中实现状态管理
- 改进消息处理逻辑
- 添加模式切换UI指示

---

## 7. 技术实现要点

### 前端状态管理
```typescript
// 在ChatWindow组件中
const [chatMode, setChatMode] = useState<'general_chat' | 'study_plan_qna' | 'practice_setup'>('general_chat');
const [practiceState, setPracticeState] = useState<PracticeState>({});
```

### 后端服务分离
```python
# 在AIChatService中
def process_message(self, account, message):
    # 意图识别
    intent = self.detect_intent(message)
    
    # 根据意图分发到不同处理器
    if intent == 'practice_setup':
        return self.handle_practice_setup(account, message)
    elif intent == 'study_plan_qna':
        return self.handle_study_plan_qna(account, message)
    else:
        return self.handle_general_chat(account, message)
```

---

## 8. 下一步行动

1. **完善意图识别逻辑** - 改进关键词匹配和上下文理解
2. **优化状态管理** - 确保模式切换的平滑性
3. **添加UI指示器** - 让用户知道当前处于哪种模式
4. **改进错误处理** - 为每种模式提供适当的错误恢复机制
5. **测试集成** - 确保三个模式能够正确切换和协作

---

**创建时间**: 2025-11-17  
**版本**: 1.0  
**状态**: 设计规范完成，待实现