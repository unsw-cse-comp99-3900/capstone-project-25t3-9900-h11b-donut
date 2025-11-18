# 智能学习计划管理系统 - API文档

## 概述

本文档详细描述了智能学习计划管理系统的所有API接口，包括前端与后端的交互规范。

## 基础信息

- **API基础路径**: `/api`
- **认证方式**: Bearer Token (Authorization: Bearer {token})
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证相关 API

### 1. 学生注册
```http
POST /api/auth/register
Content-Type: multipart/form-data

参数:
- student_id: string (学号，格式如 z1234567)
- name: string (姓名，仅允许字母)
- email: string (邮箱地址)
- password: string (8-64位，包含大小写字母、数字、特殊字符)
- avatar: File (可选，头像文件)

响应:
{
  "success": boolean,
  "message": string,
  "data": any
}
```

### 2. 管理员注册
```http
POST /api/admin/register
Content-Type: multipart/form-data

参数:
- admin_id: string (管理员ID)
- fullName: string (全名)
- email: string (邮箱地址)
- password: string (密码要求同学生)
- avatar: File (可选，头像文件)

响应:
{
  "success": boolean,
  "message": string,
  "data": any
}
```

### 3. 学生登录
```http
POST /api/auth/login
Content-Type: application/json

请求体:
{
  "student_id": string,
  "password": string
}

响应:
{
  "success": boolean,
  "data": {
    "token": string,
    "user": {
      "studentId": string,
      "name": string,
      "email": string,
      "avatarUrl": string
    }
  }
}
```

### 4. 管理员登录
```http
POST /api/admin/login
Content-Type: application/json

请求体:
{
  "admin_id": string,
  "password": string
}

响应:
{
  "success": boolean,
  "data": {
    "token": string,
    "user": {
      "adminId": string,
      "fullName": string,
      "email": string,
      "avatarUrl": string
    }
  }
}
```

### 5. 登出
```http
POST /api/auth/logout
Authorization: Bearer {token}

POST /api/admin/logout
Authorization: Bearer {token}
```

## 课程管理 API

### 1. 搜索课程
```http
GET /api/courses/search?q={keyword}

响应:
{
  "success": boolean,
  "data": [
    {
      "code": string,
      "title": string,
      "description": string,
      "illustration": "orange" | "student" | "admin"
    }
  ]
}
```

### 2. 获取可选课程列表
```http
GET /api/courses/available
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [ApiCourse]
}
```

### 3. 获取学生已选课程
```http
GET /api/courses/my
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [ApiCourse]
}
```

### 4. 加入课程
```http
POST /api/courses/add
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "courseId": string
}
```

### 5. 退出课程
```http
DELETE /api/courses/{courseId}
Authorization: Bearer {token}
```

### 6. 获取课程任务
```http
GET /api/courses/{courseCode}/tasks
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [
    {
      "id": string,
      "title": string,
      "deadline": string,
      "brief": string,
      "percent_contribution": number,
      "url": string | null
    }
  ]
}
```

### 7. 获取课程材料
```http
GET /api/courses/{courseId}/materials
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [
    {
      "id": string,
      "title": string,
      "fileType": string,
      "fileSize": string,
      "description": string,
      "uploadDate": string
    }
  ]
}
```

## 管理员课程管理 API

### 1. 获取管理员课程列表
```http
GET /api/courses_admin?admin_id={adminId}
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [ApiCourse]
}
```

### 2. 创建课程
```http
POST /api/create_course
Authorization: Bearer {token}
Content-Type: multipart/form-data

参数:
- admin_id: string
- code: string
- title: string
- description: string
- illustration: "orange" | "student" | "admin"
```

### 3. 删除课程
```http
POST /api/delete_course
Authorization: Bearer {token}
Content-Type: multipart/form-data

参数:
- admin_id: string
- code: string
```

### 4. 检查课程是否存在
```http
GET /api/course_exists?code={courseCode}
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": {
    "exists": boolean
  }
}
```

### 5. 获取课程任务（管理员）
```http
GET /api/courses_admin/{courseId}/tasks
Authorization: Bearer {token}
```

### 6. 创建任务
```http
POST /api/courses_admin/{courseId}/tasks/create
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "title": string,
  "deadline": string,
  "brief": string,
  "percent_contribution": number,
  "url": string | null
}
```

### 7. 删除任务
```http
POST /api/courses_admin/{courseId}/tasks/{taskId}/delete?delete_file={boolean}
Authorization: Bearer {token}
```

### 8. 编辑任务
```http
PUT /api/courses_admin/{courseId}/tasks/{taskId}?delete_old_file={boolean}
Authorization: Bearer {token}
Content-Type: application/json

请求体: CreateTaskPayload
```

### 9. 上传材料文件
```http
POST /api/courses_admin/upload/material-file
Authorization: Bearer {token}
Content-Type: multipart/form-data

参数:
- file: File
- course: string (courseId)
```

### 10. 创建材料
```http
POST /api/courses_admin/{courseId}/materials/create
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "title": string,
  "description": string,
  "url": string
}
```

### 11. 删除材料
```http
POST /api/courses_admin/{courseId}/materials/{materialId}/delete
Authorization: Bearer {token}
```

### 12. 更新材料
```http
POST /api/courses_admin/{courseId}/materials/{materialId}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "title": string,
  "description": string,
  "url": string
}
```

## 学习计划 API

### 1. 生成AI学习计划
```http
POST /api/generate
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": {
    "days": [
      {
        "date": "YYYY-MM-DD",
        "blocks": [
          {
            "taskId": string,
            "partId": string,
            "title": string,
            "minutes": number
          }
        ]
      }
    ],
    "aiSummary": {
      "tasks": [
        {
          "taskId": string,
          "taskTitle": string,
          "parts": []
        }
      ]
    },
    "weekStart": "YYYY-MM-DD"
  }
}
```

### 2. 保存周计划
```http
PUT /api/plans/weekly/{weekOffset}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "plan": [ApiPlanItem]
}
```

### 3. 获取周计划
```http
GET /api/plans/weekly/{weekOffset}
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [ApiPlanItem]
}
```

### 4. 获取所有周计划
```http
GET /api/weekly/all
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": Record<string, ApiPlanItem[]>
}
```

### 5. 保存学习计划到服务器
```http
POST /api/save
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "student_id": string,
  "weeklyPlans": Record<string, any[]>,
  "tz": string,
  "source": "ai"
}
```

## 用户偏好 API

### 1. 获取用户偏好
```http
GET /api/preferences
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": {
    "dailyHours": number,
    "weeklyStudyDays": number,
    "avoidDays": string[],
    "saveAsDefault": boolean,
    "description": string
  }
}
```

### 2. 保存用户偏好
```http
PUT /api/preferences
Authorization: Bearer {token}
Content-Type: application/json

请求体: ApiPreferences
```

## 任务进度 API

### 1. 更新任务进度
```http
PUT /api/tasks/{taskId}/progress
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "progress": number (0-100)
}
```

### 2. 获取学生所有任务进度
```http
GET /api/student/progress
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [
    {
      "task_id": number,
      "progress": number,
      "updated_at": string
    }
  ]
}
```

### 3. 获取课程任务进度
```http
GET /api/courses/{courseCode}/tasks/progress
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [
    {
      "task_id": number,
      "task_title": string,
      "progress": number,
      "deadline": string
    }
  ]
}
```

### 4. 获取单个任务进度详情
```http
GET /api/tasks/{taskId}/progress
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": {
    "task_id": number,
    "progress": number,
    "student_id": string
  }
}
```

## AI对话 API

### 1. 发送消息
```http
POST /api/ai/chat/?user_id={userId}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "message": string
}

响应:
{
  "success": boolean,
  "user_message": ChatMessage,
  "ai_response": ChatMessage,
  "error": string
}
```

### 2. 获取对话历史
```http
GET /api/ai/chat/?user_id={userId}&limit={number}&days={number}
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "messages": [ChatMessage],
  "error": string
}
```

### 3. 保存学习计划到AI模块
```http
POST /api/ai/study-plan/?user_id={userId}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "plan_data": any
}
```

### 4. 获取学习计划
```http
GET /api/ai/study-plan/
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "plan_data": any,
  "error": string
}
```

### 5. 清理旧数据
```http
POST /api/ai/cleanup/
Authorization: Bearer {token}
```

### 6. 问候检查
```http
GET /api/ai/greeting-check/
Authorization: Bearer {token}

响应:
{
  "should_send_greeting": boolean
}
```

### 7. AI服务健康检查
```http
GET /api/ai/health/
Authorization: Bearer {token}

响应:
{
  "success": boolean
}
```

## 消息提醒 API

### 1. 获取用户消息
```http
GET /api/reminders/{studentId}/
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [Message]
}
```

### 2. 标记消息为已读
```http
POST /api/reminders/{messageId}/mark-as-read
Authorization: Bearer {token}
```

### 3. 批量标记消息为已读
```http
POST /api/reminders/mark-as-read
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "ids": string[]
}
```

## 管理员监控 API

### 1. 获取课程学生进度
```http
GET /api/courses_admin/{courseId}/students/progress?task_id={taskId}
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "data": [
    {
      "student_id": string,
      "name": string,
      "progress": number,
      "overdue_count": number
    }
  ]
}
```

### 2. 获取学生风险报告
```http
POST /api/admin/student_risk_summary
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "course_id": string,
  "task_id": string,
  "as_of_date": string (可选)
}

响应:
{
  "success": boolean,
  "data": [
    {
      "student_id": string,
      "student_name": string,
      "overdue_parts": number,
      "consecutive_not_on_time_days": number
    }
  ]
}
```

## 材料下载 API

### 1. 下载材料
```http
GET /api/materials/{materialId}/download
Authorization: Bearer {token}

响应: Blob (文件流)
```

## 数据类型定义

### ApiCourse
```typescript
interface ApiCourse {
  id: string;
  title: string;
  description: string;
  illustration: 'orange' | 'student' | 'admin';
}
```

### ApiTask
```typescript
interface ApiTask {
  id: string;
  title: string;
  deadline: string;
  brief?: string;
  percentContribution?: number;
  url?: string | null;
}
```

### ApiPlanItem
```typescript
interface ApiPlanItem {
  id: string;
  courseId: string;
  courseTitle: string;
  partTitle: string;
  minutes: number;
  date: string;
  color: string;
  completed?: boolean;
  partIndex?: number;
  partsCount?: number;
}
```

### ApiPreferences
```typescript
interface ApiPreferences {
  dailyHours: number;
  weeklyStudyDays: number;
  avoidDays: string[];
  saveAsDefault: boolean;
  description?: string;
}
```

### ChatMessage
```typescript
interface ChatMessage {
  id: number;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
  metadata?: any;
}
```

### Message
```typescript
interface Message {
  id: string;
  type: 'due_alert' | 'nightly_notice' | 'weekly_bonus' | 'system_notification';
  title: string;
  preview: string;
  timestamp: string;
  isRead: boolean;
  courseId?: string;
  dueTime?: string;
}
```

## 错误处理

### 标准响应格式
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
}
```

### 常见错误码
- **401 Unauthorized**: 未授权，token无效或过期
- **403 Forbidden**: 权限不足
- **404 Not Found**: 资源不存在
- **422 Unprocessable Entity**: 请求参数验证失败
- **500 Internal Server Error**: 服务器内部错误

### 401特殊处理
当收到401状态码时，系统会：
1. 清空本地存储的认证信息
2. 跳转到登录页面
3. 如果是异地登录，显示提示信息

## 本地存储

### 认证相关
- `auth_token`: 用户认证token
- `login_time`: 登录时间
- `current_user_id`: 当前用户ID

### 用户数据
- `u:{userId}:user`: 用户信息缓存
- 课程数据缓存
- 偏好设置缓存

## 注意事项

1. **认证**: 除登录/注册接口外，所有API都需要在请求头中包含有效的Bearer Token
2. **时区**: 所有日期时间都使用UTC格式，前端需要根据用户时区进行转换
3. **文件上传**: 支持multipart/form-data格式，需要正确设置Content-Type
4. **分页**: 部分接口支持分页，使用limit和offset参数
5. **错误处理**: 客户端需要正确处理各种错误情况，特别是401认证失败
6. **数据验证**: 前端需要进行基础的数据验证，但最终验证以服务端为准

## AI问题生成器 API

### 概述
AI问题生成器提供智能化的练习题目生成、评分和反馈功能，支持根据学生薄弱项动态生成个性化练习题。

### 1. 上传示例题目 (管理员)
```http
POST /api/ai/sample-questions/upload
Content-Type: application/json
Authorization: Bearer {token}

请求体:
{
  "course_code": "CS101",
  "topic": "binary search",
  "questions": [
    {
      "question_text": "What is the time complexity of binary search?",
      "question_type": "multiple_choice",
      "options": ["O(n)", "O(log n)", "O(1)", "O(n^2)"],
      "correct_answer": "O(log n)",
      "explanation": "Binary search divides the search space in half each time...",
      "difficulty": "medium"
    }
  ]
}

响应:
{
  "success": boolean,
  "message": string,
  "data": any
}
```

### 2. 获取示例题目列表 (管理员)
```http
GET /api/ai/sample-questions?course_code=CS101&topic=binary%20search&page=1&page_size=20
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "message": string,
  "data": {
    "questions": [
      {
        "id": number,
        "course_code": string,
        "topic": string,
        "question_text": string,
        "question_type": "multiple_choice" | "short_answer",
        "options": string[],
        "correct_answer": string,
        "explanation": string,
        "difficulty": "easy" | "medium" | "hard",
        "created_at": string
      }
    ],
    "total": number
  }
}
```

### 3. AI生成练习题目
```http
POST /api/ai/questions/generate
Content-Type: application/json
Authorization: Bearer {token}

请求体:
{
  "course_code": "CS101",
  "topic": "binary search",
  "question_count": 5,
  "question_types": ["multiple_choice", "short_answer"],
  "difficulty": "medium",
  "sample_questions": [1, 2, 3] // 可选，示例题目ID列表
}

响应:
{
  "success": boolean,
  "message": string,
  "data": {
    "session_id": string,
    "questions": [
      {
        "id": number,
        "question_text": string,
        "question_type": "multiple_choice" | "short_answer",
        "options": string[],
        "correct_answer": string,
        "explanation": string,
        "difficulty": "easy" | "medium" | "hard"
      }
    ],
    "total_questions": number,
    "estimated_time": number
  }
}
```

### 4. 提交答案并获取AI评分
```http
POST /api/ai/answers/submit
Content-Type: application/json
Authorization: Bearer {token}

请求体:
{
  "session_id": string,
  "student_id": number,
  "answers": [
    {
      "question_id": number,
      "answer": string,
      "time_spent": number // 秒
    }
  ]
}

响应:
{
  "success": boolean,
  "message": string,
  "data": {
    "session_id": string,
    "total_score": number,
    "max_score": number,
    "percentage": number,
    "feedback": string,
    "detailed_feedback": [
      {
        "question_id": number,
        "score": number,
        "feedback": string,
        "is_correct": boolean
      }
    ],
    "time_spent": number
  }
}
```

### 5. 获取学生答题历史
```http
GET /api/ai/results?student_id=123&session_id=abc123&page=1&page_size=20
Authorization: Bearer {token}

响应:
{
  "success": boolean,
  "message": string,
  "data": {
    "results": [
      {
        "id": number,
        "session_id": string,
        "student_id": number,
        "total_score": number,
        "max_score": number,
        "percentage": number,
        "feedback": string,
        "time_spent": number,
        "completed_at": string
      }
    ],
    "total": number
  }
}
```

### 前端集成示例

#### 生成练习题目
```typescript
import { aiQuestionService } from '../services/aiQuestionService';

// 根据薄弱项生成练习题
const result = await aiQuestionService.generatePracticeQuestions(
  'CS101',
  ['binary search', 'data structures'],
  5
);

if (result.success) {
  console.log('生成的题目:', result.data.questions);
  console.log('会话ID:', result.data.session_id);
}
```

#### 提交答案获取AI评分
```typescript
const gradingResult = await aiQuestionService.submitAnswers({
  session_id: 'session_123',
  student_id: 456,
  answers: [
    {
      question_id: 1,
      answer: 'O(log n)',
      time_spent: 120
    }
  ]
});

if (gradingResult.success) {
  console.log('得分:', gradingResult.data.total_score);
  console.log('AI反馈:', gradingResult.data.feedback);
}
```

### 使用场景

1. **智能练习**: 学生在AI对话中提到薄弱项，AI自动识别并生成相关练习题
2. **个性化学习**: 根据学生的学习历史和答题表现，生成针对性的练习
3. **即时反馈**: 学生提交答案后，AI立即提供评分和个性化反馈
4. **学习分析**: 通过答题历史分析学生的学习进度和掌握情况

### 注意事项

1. **题目类型**: 支持选择题(multiple_choice)和简答题(short_answer)
2. **难度等级**: 支持easy、medium、hard三个难度等级
3. **会话管理**: 每次练习生成唯一的session_id，用于跟踪答题过程
4. **AI评分**: 简答题由AI进行语义分析和评分，选择题自动评分
5. **错误处理**: 所有API都包含完善的错误处理和反馈机制
6. **🆕 题目来源**: AI现在从courses_admin的Question表读取管理员上传的题目，无需单独上传示例题目

## 更新日志

- **v1.0.0** (2025-11-12): 初始版本，包含所有核心API接口
- **v1.1.0** (2025-11-16): 新增AI问题生成器API，支持智能练习题目生成和AI评分
- **v1.2.0** (2025-11-16): AI生成器现在从courses_admin Question表读取题目，与前端题库管理完全集成
- 后续版本更新将在此记录