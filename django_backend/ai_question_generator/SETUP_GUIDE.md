# AI Question Generator & Grader - Django集成设置指南

## 📦 安装步骤

### 1. 安装依赖

```bash
cd django_backend
pip install -r requirements.txt
```

新增的依赖：
- `google-generativeai==0.8.3` - Gemini API
- `typing-extensions>=4.5.0` - 类型支持

### 2. 配置环境变量

确保 `django_backend/.env` 文件包含：
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**获取API密钥**：
1. 访问 https://aistudio.google.com/app/apikey
2. 创建或复制API密钥
3. 更新`.env`文件

### 3. 运行数据库迁移

```bash
python manage.py makemigrations ai_question_generator
python manage.py migrate
```

这将创建以下数据表：
- `ai_sample_question` - 示例题目模板
- `ai_generated_question` - AI生成的题目
- `ai_student_answer` - 学生答案和评分结果

### 4. 加载测试数据

```bash
python manage.py load_sample_questions
```

这将加载：
- Python Data Structures 示例（2题）
- Machine Learning Basics 示例（2题）

### 5. 启动Django服务器

```bash
python manage.py runserver
```

服务运行在 `http://localhost:8000`

---

## 🧪 测试API

### 方法1: 使用测试脚本

```bash
python ai_question_generator/test_api.py
```

这将测试完整流程：
1. 查看示例题目
2. AI生成新题目
3. 提交学生答案
4. AI自动评分
5. 查询历史成绩

### 方法2: 使用curl

#### 查看示例题目
```bash
curl "http://localhost:8000/api/ai/sample-questions?course_code=COMP9900"
```

#### 生成题目
```bash
curl -X POST http://localhost:8000/api/ai/questions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "course_code": "COMP9900",
    "topic": "Database Normalization",
    "difficulty": "medium",
    "count": 5,
    "mcq_count": 3,
    "short_answer_count": 2
  }'
```

#### 提交答案
```bash
curl -X POST http://localhost:8000/api/ai/answers/submit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "student_id": "z1234567",
    "answers": [
      {"question_db_id": 101, "answer": "A"},
      {"question_db_id": 102, "answer": "Normalization reduces redundancy..."}
    ]
  }'
```

---

## 📚 API接口

### 完整API文档
查看 `API_DOCUMENTATION.md` 获取详细的API文档。

### 快速参考

| 功能 | 方法 | 端点 |
|------|------|------|
| 上传示例题目 | POST | `/api/ai/sample-questions/upload` |
| 查看示例题目 | GET | `/api/ai/sample-questions` |
| 生成题目 | POST | `/api/ai/questions/generate` |
| 提交答案评分 | POST | `/api/ai/answers/submit` |
| 查询历史成绩 | GET | `/api/ai/results` |

---

## 🗄️ 数据模型

### Admin上传示例题目
通过Admin界面或API上传示例题目到`SampleQuestion`表。

### 学生使用流程
1. 前端请求生成题目 → 后端从数据库读取示例 → AI生成新题目 → 保存到`GeneratedQuestion`表
2. 学生答题 → 前端提交答案
3. 后端AI评分 → 保存到`StudentAnswer`表 → 返回评分结果

---

## 🔧 Django Admin管理

访问 `http://localhost:8000/admin` 可以管理：
- **Sample Questions** - 查看/编辑示例题目
- **Generated Questions** - 查看AI生成的题目
- **Student Answers** - 查看学生答案和评分

---

## 📁 文件结构

```
ai_question_generator/
├── models.py                 # 数据模型
├── views.py                  # API视图
├── urls.py                   # URL路由
├── admin.py                  # Admin配置
├── generator.py              # AI题目生成器
├── grader.py                 # AI自动评分器
├── utils.py                  # 工具函数
├── test_api.py               # API测试脚本
├── API_DOCUMENTATION.md      # 完整API文档
├── SETUP_GUIDE.md            # 本文档
└── management/
    └── commands/
        └── load_sample_questions.py  # 测试数据加载命令
```

---

## 🎯 关键特性

### 1. 跨主题生成
- 使用Python示例可以生成Machine Learning题目
- AI只模仿示例的**风格、格式、难度**，不复制内容

### 2. 评分一致性
- 相同答案每次得分相同
- Temperature设置为0.1确保稳定性

### 3. 个性化反馈
- **Hint**: 根据学生具体错误生成提示
- **Solution**: 提供完整解答和改进建议
- **Breakdown**: 详细的评分细节（Correctness, Completeness, Clarity）

### 4. 数据持久化
- 所有生成的题目保存到数据库
- 所有答案和评分结果保存到数据库
- 支持历史查询和分析

---

## ⚠️ 注意事项

1. **API密钥安全**: 
   - 不要将`.env`文件提交到Git
   - 生产环境使用环境变量

2. **数据库迁移**:
   - 首次使用必须运行migrations
   - 修改models后重新运行migrations

3. **示例题目要求**:
   - 至少上传2-3个示例题目
   - 示例质量直接影响生成质量

4. **评分时间**:
   - 简答题AI评分需要2-5秒
   - 选择题评分即时

---

## 🐛 故障排除

### 问题1: API密钥错误
```
❌ 错误: 未找到 GEMINI_API_KEY
```
**解决**: 检查`.env`文件是否包含`GEMINI_API_KEY=...`

### 问题2: 无法生成题目
```
No sample questions found for course COMP9900
```
**解决**: 运行 `python manage.py load_sample_questions`

### 问题3: 数据库错误
```
no such table: ai_sample_question
```
**解决**: 运行 `python manage.py migrate`

### 问题4: 导入错误
```
ModuleNotFoundError: No module named 'google.generativeai'
```
**解决**: 运行 `pip install -r requirements.txt`

---

## 📊 性能优化建议

1. **缓存生成的题目**: 相同参数的请求可复用
2. **批量评分**: 多个学生答案可并发评分
3. **数据库索引**: 已为常用查询添加索引
4. **异步处理**: 评分任务可改为异步队列

---

## 🔄 后续扩展

### 计划功能
- [ ] 题目难度动态调整
- [ ] 学生表现分析仪表板
- [ ] 题库智能推荐
- [ ] 多语言支持
- [ ] 图片/代码题型支持

---

**需要帮助?** 查看 `API_DOCUMENTATION.md` 或运行 `python ai_question_generator/test_api.py`

---

**Version**: 1.0  
**Last Updated**: 2025-11-15
