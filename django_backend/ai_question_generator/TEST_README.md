# AI Question Generator - 测试文件说明

## 📁 文件结构

```
ai_question_generator/
├── test_api.py           ⭐ 主测试脚本（运行这个）
├── HOW_TO_TEST.md        📖 测试指南
├── generator.py          🤖 AI题目生成器
├── grader.py            🤖 AI自动评分器
├── views.py             🌐 API视图
├── models.py            💾 数据模型
├── urls.py              🔗 URL路由
└── management/
    └── commands/
        └── load_sample_questions.py  📥 加载测试数据
```

## 🚀 快速测试

### 1️⃣ 加载测试数据
```bash
python manage.py load_sample_questions
```

### 2️⃣ 启动服务器
```bash
python manage.py runserver
```

### 3️⃣ 运行测试（新终端）
```bash
python ai_question_generator/test_api.py
```

## 📊 测试覆盖

| 测试 | API端点 | 功能 |
|------|---------|------|
| 1️⃣ | `GET /api/ai/sample-questions` | 获取示例题目 |
| 2️⃣ | `POST /api/ai/questions/generate` | AI生成题目 |
| 3️⃣ | `POST /api/ai/answers/submit` | 提交答案并AI评分 |
| 4️⃣ | `GET /api/ai/results` | 查询历史成绩 |

## 🎯 预期结果

✅ 测试1: 返回4个示例题目（Python + ML）  
✅ 测试2: 生成5道新题目（Neural Networks主题）  
✅ 测试3: AI评分并返回详细反馈  
✅ 测试4: 返回学生的所有答题记录  

## 📚 详细文档

- **HOW_TO_TEST.md** - 完整的测试指南
- **API_DOCUMENTATION.md** - API接口文档
- **SETUP_GUIDE.md** - 安装和配置指南

## ⚡ 性能

- 总测试时间: 约30-45秒
- AI生成: 10-15秒
- AI评分: 15-30秒

## 🐛 遇到问题？

查看 `HOW_TO_TEST.md` 的常见问题部分
