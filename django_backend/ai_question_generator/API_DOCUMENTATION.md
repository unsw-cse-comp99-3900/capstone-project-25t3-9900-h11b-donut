# AI Question Generator & Grader API Documentation

## 概述

AI题目生成与自动评分系统API，支持：
- **从courses_admin Question表读取题目**（前端已上传的题目）
- 基于现有题目AI生成新题目（支持跨主题）
- 学生提交答案并获得AI自动评分
- 个性化hint和solution生成

## 🆕 重要更新

**AI现在从courses_admin的Question表读取题目**，而不是从独立的SampleQuestion表。这意味着：

- ✅ 管理员可以通过前端AdminManageCourse页面上传题目
- ✅ AI会自动使用这些上传的题目作为生成参考
- ✅ 支持关键词匹配和主题搜索
- ✅ 无需额外的题目上传步骤

## Base URL

```
http://localhost:8000/api/ai
```

---

## 1. 示例题目管理

### 1.1 上传示例题目

Admin上传示例题目到数据库，用于AI生成参考。

**Endpoint**: `POST /api/ai/sample-questions/upload`

**Request Body**:
```json
{
  "course_code": "COMP9900",
  "topic": "Python Data Structures",
  "difficulty": "medium",
  "questions": [
    {
      "type": "mcq",
      "question": "What is the time complexity of...",
      "options": [
        "A. O(1)",
        "B. O(n)",
        "C. O(log n)",
        "D. O(n²)"
      ],
      "correct_answer": "A",
      "explanation": "List access by index is O(1)...",
      "score": 10
    },
    {
      "type": "short_answer",
      "question": "Explain the difference between...",
      "sample_answer": "The main differences are: 1) Mutability...",
      "grading_points": [
        "Mutability difference",
        "Performance comparison",
        "Syntax difference"
      ],
      "score": 10
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Uploaded 2 sample questions",
  "question_ids": [1, 2]
}
```

---

### 1.2 获取示例题目

查看数据库中的示例题目（Admin用）。

**Endpoint**: `GET /api/ai/sample-questions`

**Query Parameters**:
- `course_code` (optional): 课程代码
- `topic` (optional): 主题（模糊搜索）

**Example**:
```
GET /api/ai/sample-questions?course_code=COMP9900&topic=Python
```

**Response**:
```json
{
  "success": true,
  "questions": [
    {
      "id": 1,
      "course_code": "COMP9900",
      "topic": "Python Data Structures",
      "difficulty": "medium",
      "question_type": "mcq",
      "question_text": "What is...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "...",
      "score": 10,
      "created_at": "2025-11-15T10:00:00Z",
      "is_active": true
    }
  ]
}
```

---

## 2. AI题目生成

### 2.1 生成题目

基于数据库中的示例题目，AI生成新题目。

**Endpoint**: `POST /api/ai/questions/generate`

**Request Body**:
```json
{
  "course_code": "COMP9900",
  "topic": "Machine Learning Basics",
  "difficulty": "medium",
  "count": 5,
  "mcq_count": 3,
  "short_answer_count": 2
}
```

**字段说明**:
- `course_code`: 课程代码（必需，用于查找示例题目）
- `topic`: 目标主题（必需，可与示例题目主题不同）
- `difficulty`: 难度等级（可选，默认medium）
- `count`: 总题目数（可选，默认5）
- `mcq_count`: 选择题数量（可选，默认3）
- `short_answer_count`: 简答题数量（可选，默认2）

**Response**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "questions": [
    {
      "db_id": 101,
      "question_id": 1,
      "type": "mcq",
      "question": "What is the primary purpose of...",
      "options": [
        "A. To determine the batch size",
        "B. To control the step size",
        "C. To set the number of epochs",
        "D. To initialize weights"
      ],
      "correct_answer": "B",
      "explanation": "The learning rate controls...",
      "difficulty": "medium",
      "topic": "Machine Learning Basics",
      "score": 10
    },
    {
      "db_id": 102,
      "question_id": 2,
      "type": "short_answer",
      "question": "Explain what happens when...",
      "sample_answer": "When the learning rate is too high...",
      "grading_points": [
        "High learning rate causes overshooting",
        "Low learning rate causes slow convergence"
      ],
      "difficulty": "medium",
      "topic": "Machine Learning Basics",
      "score": 10
    }
  ],
  "total_questions": 5
}
```

**重要说明**:
- `session_id`: 生成会话ID，提交答案时需要
- `db_id`: 数据库中的题目ID，提交答案时需要
- `question_id`: 前端显示用的序号（1, 2, 3...）
- 题目已保存到数据库，可复用

---

## 3. 学生答题与评分

### 3.1 提交答案并评分

学生提交答案，后端调用AI进行自动评分。

**Endpoint**: `POST /api/ai/answers/submit`

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "student_id": "z1234567",
  "answers": [
    {
      "question_db_id": 101,
      "answer": "B"
    },
    {
      "question_db_id": 102,
      "answer": "Learning rate controls how much we update the model weights during training. If it's too high, training might not converge. If it's too low, training will be very slow."
    }
  ]
}
```

**字段说明**:
- `session_id`: 生成题目时返回的会话ID
- `student_id`: 学生ID
- `answers`: 答案数组
  - `question_db_id`: 题目的数据库ID（即生成时返回的`db_id`）
  - `answer`: 学生答案（选择题填字母，简答题填文本）

**Response**:
```json
{
  "success": true,
  "student_id": "z1234567",
  "grading_results": [
    {
      "question_id": 101,
      "question_db_id": 101,
      "type": "mcq",
      "student_answer": "B",
      "score": 10,
      "max_score": 10,
      "is_correct": true,
      "feedback": "Correct! The learning rate controls the step size when updating model parameters."
    },
    {
      "question_id": 102,
      "question_db_id": 102,
      "type": "short_answer",
      "student_answer": "Learning rate controls how much we update...",
      "score": 7.5,
      "max_score": 10,
      "breakdown": {
        "Correctness": 3,
        "Completeness": 3,
        "Clarity": 2
      },
      "feedback": "Good explanation of the basic concept. You correctly identified what happens when the learning rate is too high and too low. However, you could provide more details about the specific consequences...",
      "hint": "Consider discussing: 1) What exactly happens during overshooting (oscillation, divergence), 2) The impact on convergence speed with low learning rate, 3) How learning rate affects the ability to escape local minima.",
      "solution": "A complete answer should include: 1) High learning rate causes parameter updates to overshoot optimal values, leading to oscillation around the minimum or complete divergence. The loss may increase instead of decrease. 2) Low learning rate results in very small parameter updates, requiring many more iterations to converge. This significantly increases training time. 3) Low learning rate may cause the model to get stuck in local minima or saddle points, preventing it from finding the global optimum."
    }
  ],
  "total_score": 17.5,
  "total_max_score": 20,
  "percentage": 87.5
}
```

**评分说明**:

**选择题（MCQ）**:
- `is_correct`: 是否正确
- `score`: 10分（正确）或 0分（错误）
- `feedback`: 正确答案的解释

**简答题（Short Answer）**:
- `breakdown`: 评分细节
  - `Correctness`: 0-4分（概念准确性）
  - `Completeness`: 0-4分（要点覆盖度）
  - `Clarity`: 0-2分（表达清晰度）
- `score`: 总分（breakdown之和）
- `feedback`: 详细反馈
- `hint`: 个性化提示（根据学生具体错误生成）
- `solution`: 完整解答（告诉学生应该包含哪些内容）

---

### 3.2 获取学生历史成绩

查询学生的答题历史和评分记录。

**Endpoint**: `GET /api/ai/results`

**Query Parameters**:
- `student_id` (required): 学生ID
- `session_id` (optional): 会话ID（查询特定一次答题）

**Example**:
```
GET /api/ai/results?student_id=z1234567
GET /api/ai/results?student_id=z1234567&session_id=550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "question_id": 101,
      "question_data": {
        "type": "mcq",
        "question": "...",
        "options": [...],
        "correct_answer": "B"
      },
      "answer_text": "B",
      "grading_result": {
        "score": 10,
        "max_score": 10,
        "is_correct": true,
        "feedback": "..."
      },
      "submitted_at": "2025-11-15T10:30:00Z",
      "graded_at": "2025-11-15T10:30:05Z"
    }
  ]
}
```

---

## 4. 数据模型

### SampleQuestion (示例题目)
```python
{
  "id": 1,
  "course_code": "COMP9900",
  "topic": "Python Data Structures",
  "difficulty": "medium",
  "question_type": "mcq" | "short_answer",
  "question_text": "题目内容",
  
  # MCQ字段
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_answer": "A",
  "explanation": "解释",
  
  # Short Answer字段
  "sample_answer": "参考答案",
  "grading_points": ["要点1", "要点2"],
  
  "score": 10,
  "created_by": "admin_id",
  "created_at": "2025-11-15T10:00:00Z",
  "is_active": true
}
```

### GeneratedQuestion (生成的题目)
```python
{
  "id": 101,
  "session_id": "uuid-...",
  "course_code": "COMP9900",
  "topic": "Machine Learning",
  "difficulty": "medium",
  "question_type": "mcq" | "short_answer",
  "question_data": {
    # 完整题目JSON（格式同SampleQuestion）
  },
  "created_at": "2025-11-15T10:15:00Z"
}
```

### StudentAnswer (学生答案)
```python
{
  "id": 1,
  "session_id": "uuid-...",
  "student_id": "z1234567",
  "question_id": 101,
  "answer_text": "学生答案",
  "grading_result": {
    "score": 8.5,
    "max_score": 10,
    "breakdown": {...},
    "feedback": "...",
    "hint": "...",
    "solution": "..."
  },
  "submitted_at": "2025-11-15T10:30:00Z",
  "graded_at": "2025-11-15T10:30:05Z"
}
```

---

## 5. 使用流程

### Admin流程
1. 上传示例题目到数据库
   ```
   POST /api/ai/sample-questions/upload
   ```
2. 查看已上传的示例题目
   ```
   GET /api/ai/sample-questions?course_code=COMP9900
   ```

### 学生答题流程
1. 前端请求生成题目
   ```
   POST /api/ai/questions/generate
   {
     "course_code": "COMP9900",
     "topic": "Machine Learning",
     "count": 5
   }
   ```
   
2. 后端返回题目和session_id
   ```json
   {
     "session_id": "uuid-...",
     "questions": [...]
   }
   ```
   
3. 学生答题，前端收集答案

4. 前端提交答案
   ```
   POST /api/ai/answers/submit
   {
     "session_id": "uuid-...",
     "student_id": "z1234567",
     "answers": [...]
   }
   ```
   
5. 后端AI评分并返回结果
   ```json
   {
     "grading_results": [...],
     "total_score": 42.5,
     "percentage": 85.0
   }
   ```

---

## 6. 错误处理

所有API在失败时返回：
```json
{
  "success": false,
  "error": "错误信息",
  "traceback": "详细堆栈（仅开发模式）"
}
```

常见错误：
- `400`: 缺少必需参数
- `404`: 未找到数据（如session_id不存在）
- `500`: 服务器内部错误（如AI API调用失败）

---

## 7. 测试

### 使用Django管理命令加载测试数据
```bash
python manage.py load_sample_questions
```

### 使用测试脚本
```bash
python ai_question_generator/test_api.py
```

---

## 8. 注意事项

1. **API密钥**: 确保`.env`文件中配置了`GEMINI_API_KEY`
2. **跨主题生成**: 可以用Python示例生成Machine Learning题目
3. **评分一致性**: 相同答案每次得分相同（temperature=0.1）
4. **数据持久化**: 所有题目和答案都保存到数据库
5. **会话管理**: 使用session_id关联一次答题的所有题目

---

**Version**: 1.0  
**Last Updated**: 2025-11-15
