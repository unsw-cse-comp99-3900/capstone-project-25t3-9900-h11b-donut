# AI Module 返回数据结构文档

## 概述
`ai_module.plan_generator.generate_plan()` 函数返回的完整JSON数据结构说明。

## 函数调用
```python
from ai_module.plan_generator import generate_plan

# 输入参数
preferences = {
    "daily_hour_cap": 3,        # 每日学习小时数
    "weekly_study_days": 5,     # 每周学习天数
    "avoid_days": [5, 6]        # 避开的日期 (0=周一, 6=周日)
}

tasks_meta = [
    {
        "id": "9517_a1",
        "task": "COMP9517 - Assignment 1",
        "dueDate": "2025-10-25",
        "detailPdfPath": "/path/to/assignment.pdf"  # 可选
    },
    # ... 更多任务
]

# 调用函数
result = generate_plan(preferences, tasks_meta)
```

## 返回数据结构

### 顶层结构
```json
{
    "ok": true,                           // 是否成功生成计划
    "relaxation": "none",                 // 调度状态 ("none", "expand-days-per-week", "allow-avoid-days", "max10h", "impossible")
    "weekStart": "2025-10-13",           // 计划开始周的周一日期
    "days": [...],                       // 每日详细安排 (见下方)
    "taskSummary": [...],                // 任务摘要 (见下方)
    "aiSummary": {...}                   // AI分析详情 (见下方)
}
```

### 1. days[] - 每日详细安排
```json
"days": [
    {
        "date": "2025-10-14",            // 日期 (YYYY-MM-DD)
        "blocks": [                      // 该日的学习任务块
            {
                "taskId": "9517_a1",     // 任务ID
                "partId": "p1",          // 部分ID
                "title": "环境配置与Snort安装",  // 任务块标题
                "minutes": 60,           // 时长(分钟)
                "reason": "within-preference"  // 调度原因
            },
            {
                "taskId": "9900_a1",
                "partId": "p1", 
                "title": "后端规划与数据库设计",
                "minutes": 60,
                "reason": "within-preference"
            }
        ]
    },
    {
        "date": "2025-10-15",
        "blocks": [...]                  // 下一天的安排
    }
]
```

### 2. taskSummary[] - 任务摘要
```json
"taskSummary": [
    {
        "taskId": "9517_a1",             // 任务ID
        "taskTitle": "COMP9517 - Assignment 1",  // 任务标题
        "totalMinutes": 300,             // 总时长(分钟)
        "parts": [                       // 部分信息(含百分比)
            {
                "partId": "p1",
                "order": 1,
                "minutes": 60,
                "percent": 20.0          // 占该任务的百分比
            },
            {
                "partId": "p2", 
                "order": 2,
                "minutes": 60,
                "percent": 20.0
            }
        ]
    }
]
```

### 3. aiSummary - AI分析详情 (最重要)
```json
"aiSummary": {
    "tasks": [
        {
            "taskId": "9517_a1",                    // 任务ID
            "taskTitle": "COMP9517 - Assignment 1", // 任务标题
            "totalMinutes": 300,                    // 总时长(分钟) = 5小时
            "explanation": "This cybersecurity lab focuses on implementing Snort IDS for network monitoring. The progression starts with environment setup and basic configuration, moves to developing custom detection rules, includes practical attack simulation for testing, and concludes with comprehensive analysis of the collected security data.",  // AI划分说明
            "parts": [                              // 详细的部分拆分
                {
                    "partId": "p1",                 // 部分ID
                    "order": 1,                     // 执行顺序
                    "title": "环境配置与Snort安装",    // 部分标题
                    "minutes": 60,                  // 时长(分钟)
                    "notes": "Install and configure Snort IDS, set up network monitoring environment, verify basic functionality", // 详细说明
                    "percent": 20.0                 // 占该任务的百分比
                },
                {
                    "partId": "p2",
                    "order": 2, 
                    "title": "自定义检测规则开发",
                    "minutes": 60,
                    "notes": "Develop custom Snort rules for specific attack patterns, test rule effectiveness",
                    "percent": 20.0
                },
                {
                    "partId": "p3",
                    "order": 3,
                    "title": "攻击模拟与测试", 
                    "minutes": 60,
                    "notes": "Simulate various network attacks, test detection capabilities, analyze alert generation",
                    "percent": 20.0
                },
                {
                    "partId": "p4",
                    "order": 4,
                    "title": "数据分析与报告",
                    "minutes": 60,
                    "notes": "Analyze collected security data, generate comprehensive report with findings and recommendations",
                    "percent": 20.0
                },
                {
                    "partId": "p5",
                    "order": 5,
                    "title": "最终审查与提交",
                    "minutes": 60, 
                    "notes": "Final review of all components, prepare submission materials, ensure completeness",
                    "percent": 20.0
                }
            ]
        }
    ]
}
```

## 错误情况
```json
{
    "ok": false,
    "message": "No course tasks found — cannot generate a plan."
}
```

或

```json
{
    "ok": false,
    "relaxation": "impossible",
    "message": "Insufficient time — cannot generate plan.",
    "unplaceableParts": [
        {
            "taskId": "9417_a3",
            "partId": "p6",
            "title": "最终报告撰写",
            "minutes_remaining": 60,
            "dueDate": "2025-12-30"
        }
    ],
    "weekStart": "2025-10-13"
}
```

## 关键信息总结

### 前端可以获取的所有信息：
1. **每个任务的完整分析** (`aiSummary.tasks[]`)
   - 总时长、AI解释说明
   - 详细的部分拆分(title, minutes, notes, percent)

2. **完整的日程安排** (`days[]`)
   - 每天的具体安排
   - 每个时间块的任务和时长

3. **任务摘要统计** (`taskSummary[]`)
   - 每个任务的总体信息
   - 部分的百分比分配

4. **调度状态信息**
   - 是否符合学生偏好
   - 是否需要放松约束条件

### 用途：
- **课程概览页面**: 使用 `taskSummary` 和 `aiSummary`
- **日历视图**: 使用 `days[]`
- **任务详情页面**: 使用 `aiSummary.tasks[].parts[]`
- **进度跟踪**: 使用 `days[].blocks[]` 的 taskId 和 partId
- **AI对话上下文**: 使用 `aiSummary.tasks[].explanation` 和 `parts[].notes`

## 示例完整返回数据
参考 `text_run.py` 的测试输出获取完整的真实数据示例。