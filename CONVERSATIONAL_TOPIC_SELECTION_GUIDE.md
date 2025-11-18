# 对话式Topic选择功能指南

## 功能概述

实现了智能的对话式topic选择功能，用户可以通过自然对话的方式选择想要练习的topic，而不需要点击按钮。

## 工作流程

### 1. 触发Topic选择
当用户提到具体的课程代码时，AI会自动显示该课程的所有可用topics：

**用户输入示例：**
- "I need help with COMP9417"
- "I'm struggling with COMP9900" 
- "I'm weak in COMP9331"

**AI回复格式：**
```
Great! I can help you with COMP9417. 🎯

Here are the available topics for COMP9417:
1. Data Mining (3 questions)
2. Algorithms (1 questions)
3. Goals (1 questions)
4. Unsupervised Learning (1 questions)
5. Clustering (1 questions)
6. Classification (1 questions)
7. Concepts (1 questions)

Please tell me which specific topic you'd like to practice. For example, you could say:
"I want to practice data mining" or "I need help with data mining"
```

### 2. 用户选择Topic
用户可以直接回复想要练习的topic名称：

**用户输入示例：**
- "data mining"
- "clustering"
- "I want to practice algorithms"
- "help with classification"

**AI回复：**
- 如果topic有效：生成练习会话按钮
- 如果topic无效：提示用户重新选择

### 3. 开始练习
AI会为选定的topic生成专门的练习会话，包含相关的练习题目。

## 技术实现

### 后端修改

1. **AIChatService类更新**
   - 修改了 `generate_course_topic_selection()` 方法，使用对话形式展示topics
   - 新增了 `extract_topic_from_response()` 方法，从用户回复中提取topic
   - 更新了 `process_message()` 方法，处理topic选择流程

2. **意图检测增强**
   - 改进了topic提取模式，支持更多表达方式
   - 增强了课程代码识别功能

3. **对话历史管理**
   - 实现了基于对话历史的上下文理解
   - 支持连续的topic选择对话

### 前端修改

1. **ChatWindow组件更新**
   - 移除了不再需要的 `selectTopic` 函数
   - 保持了 `startPracticeSession` 函数用于练习会话

## 支持的课程和Topics

### COMP9417 (Data Mining)
- Data Mining (3 questions)
- Algorithms (1 questions)
- Classification (1 questions)
- Clustering (1 questions)
- Unsupervised Learning (1 questions)
- Concepts (1 questions)
- Goals (1 questions)

### COMP9900 (Capstone)
- Capstone (2 questions)
- Collaboration (1 questions)
- Planning (1 questions)
- Project Management (1 questions)
- Teamwork (1 questions)

### COMP9331 (Networking)
- Networking (2 questions)
- OSI Model (1 questions)
- Protocols (1 questions)
- TCP (1 questions)
- Transport Layer (1 questions)
- UDP (1 questions)

### COMP1234 (Testing)
- Software Quality (1 questions)
- Testing (1 questions)
- Unit Testing (1 questions)

## 测试验证

### 功能测试
✅ 课程代码识别正常
✅ Topic列表显示正确
✅ Topic选择回复处理正常
✅ 练习会话生成成功
✅ 无效Topic处理正确

### 测试用例
```python
# 测试触发topic选择
"I need help with COMP9417" → 显示topic列表

# 测试topic选择
"data mining" → 生成练习会话
"clustering" → 生成练习会话
"invalid topic" → 提示重新选择
```

## 用户体验优势

1. **自然对话**：用户可以用自然语言表达需求
2. **智能识别**：AI能理解各种表达方式
3. **上下文感知**：基于对话历史提供连贯的体验
4. **即时反馈**：对无效输入提供清晰的指导

## 部署状态

- ✅ 后端服务运行在 http://127.0.0.1:8000/
- ✅ 前端服务运行在 http://localhost:5177/
- ✅ 数据库包含完整的测试题目
- ✅ AI服务集成正常

## 使用方法

1. 访问 http://localhost:5177/
2. 使用测试账号登录（如 z1234567）
3. 进入Chat页面
4. 输入包含课程代码的消息，如 "I need help with COMP9417"
5. 根据显示的topic列表，回复想要练习的topic名称
6. 点击生成的练习按钮开始练习

功能已完全实现并可正常使用！