# AI Question Generator & Auto-Grader

AI驱动的题目生成和自动评分系统，完全集成到Django后端。

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行迁移
python manage.py makemigrations ai_question_generator
python manage.py migrate

# 3. 加载测试数据
python manage.py load_sample_questions

# 4. 启动服务器
python manage.py runserver

# 5. 测试API
python ai_question_generator/test_api.py
```

## 📋 核心功能

### 1. Admin上传示例题目
- 通过API或Django Admin上传示例题目到数据库
- 支持选择题（MCQ）和简答题（Short Answer）
- 示例题目用于AI生成参考

### 2. AI题目生成
- 基于数据库中的示例题目，AI生成新题目
- **支持跨主题生成**：用Python示例生成Machine Learning题目
- 生成的题目自动保存到数据库

### 3. 自动评分
- 选择题：自动比对答案（10分或0分）
- 简答题：AI智能评分（0-4-2评分标准）
  - Correctness: 0-4分
  - Completeness: 0-4分
  - Clarity: 0-2分

### 4. 个性化反馈
- **Hint**: 根据学生具体错误生成个性化提示
- **Solution**: 提供完整解答和改进建议
- **Feedback**: 详细的评分反馈

## 🔌 API接口

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/ai/sample-questions/upload` | POST | Admin上传示例题目 |
| `/api/ai/sample-questions` | GET | 查看示例题目 |
| `/api/ai/questions/generate` | POST | AI生成题目 |
| `/api/ai/answers/submit` | POST | 提交答案并评分 |
| `/api/ai/results` | GET | 查询历史成绩 |

详细文档见 `API_DOCUMENTATION.md`

## 📊 使用流程

```
Admin端:
1. 上传示例题目到数据库
   POST /api/ai/sample-questions/upload

学生端:
1. 前端请求生成题目
   POST /api/ai/questions/generate
   → 返回 session_id 和 questions

2. 学生答题（前端收集答案）

3. 提交答案
   POST /api/ai/answers/submit
   → AI自动评分
   → 返回 grading_results (含hint和solution)

4. 查看历史成绩
   GET /api/ai/results?student_id=z1234567
```

## 🗄️ 数据模型

- **SampleQuestion**: Admin上传的示例题目模板
- **GeneratedQuestion**: AI生成的题目
- **StudentAnswer**: 学生答案和评分结果

所有数据持久化到数据库，支持历史查询。

## 🎯 技术特点

- ✅ **Django集成**: 使用Django的.env和ORM
- ✅ **跨主题生成**: 灵活的AI生成能力
- ✅ **评分一致性**: temperature=0.1确保稳定
- ✅ **数据持久化**: 完整的数据库支持
- ✅ **RESTful API**: 标准的JSON API
- ✅ **测试覆盖**: 完整的测试脚本

## 📁 核心文件

```
ai_question_generator/
├── models.py           # Django数据模型
├── views.py            # API视图
├── generator.py        # AI生成器
├── grader.py           # AI评分器
├── test_api.py         # API测试
└── management/
    └── commands/
        └── load_sample_questions.py  # 测试数据
```

## 📖 文档

- **SETUP_GUIDE.md** - 详细安装和配置指南
- **API_DOCUMENTATION.md** - 完整API文档
- **README.md** - 本文档

## ⚙️ 配置

确保 `django_backend/.env` 包含：
```env
GEMINI_API_KEY=your_api_key_here
```

## 🧪 测试

```bash
# 运行测试脚本
python ai_question_generator/test_api.py

# 或使用Django Admin
http://localhost:8000/admin
```

---

**需要帮助？** 查看 `SETUP_GUIDE.md` 或 `API_DOCUMENTATION.md`

**Version**: 1.0  
**Last Updated**: 2025-11-15
