# Task Progress 功能重构说明

## 概述
本次重构将task_progress功能从courses应用中独立出来，创建了专门的task_progress应用，实现了前后端分离的架构。

## 后端更改

### 1. 创建独立的task_progress应用
- **位置**: `django_backend/task_progress/`
- **包含文件**:
  - `__init__.py` - 应用初始化
  - `apps.py` - 应用配置
  - `models.py` - TaskProgress模型定义
  - `views.py` - 视图函数
  - `urls.py` - URL路由配置
  - `migrations/0001_initial.py` - 数据库迁移文件

### 2. TaskProgress模型优化
- 添加了`updated_at`字段，记录进度更新时间
- 添加了数据库索引，提高查询性能
- 保持了与原有数据库表的兼容性

### 3. 新增API端点
- `GET /api/tasks/{task_id}/progress` - 获取单个任务进度
- `PUT /api/tasks/{task_id}/progress` - 更新任务进度
- `GET /api/student/progress` - 获取学生所有任务进度
- `GET /api/courses/{course_code}/tasks/progress` - 获取课程下所有任务进度

### 4. 项目配置更新
- 在`settings.py`的`INSTALLED_APPS`中添加了`task_progress`
- 在`urls.py`中添加了task_progress的路由包含

### 5. 原有功能清理
- 移除了courses应用中重复的TaskProgress模型定义
- 保留了courses应用中task_progress视图的向后兼容性（重定向到新应用）

## 前端更改

### 1. API服务扩展
在`front_end/src/services/api.ts`中添加了新的API方法：
- `getStudentTaskProgress()` - 获取学生所有任务进度
- `getCourseTasksProgress(courseCode)` - 获取课程任务进度
- `getTaskProgressDetail(taskId)` - 获取任务进度详情

### 2. 保持兼容性
- 原有的`updateTaskProgress()`方法保持不变
- 所有现有功能继续正常工作

## 架构优势

1. **职责分离**: task_progress功能独立，便于维护和扩展
2. **性能优化**: 添加了数据库索引，提高查询效率
3. **功能增强**: 新增了批量查询和课程级别的进度查询
4. **向后兼容**: 原有API接口继续正常工作
5. **错误处理**: 增强了异常处理和错误响应

## 数据流说明

1. 前端计算任务进度
2. 通过API将进度数据发送到后端
3. 后端仅负责数据存储和查询，不进行计算
4. 前端根据需要从后端获取进度数据进行展示

## 使用示例

### 更新任务进度
```javascript
await apiService.updateTaskProgress('123', 75);
```

### 获取学生所有任务进度
```javascript
const progressList = await apiService.getStudentTaskProgress();
```

### 获取课程任务进度
```javascript
const courseProgress = await apiService.getCourseTasksProgress('COMP9900');
```

## 注意事项

1. 数据库迁移需要执行：`python manage.py migrate task_progress`
2. 原有的task_progress数据表结构保持不变，确保数据兼容性
3. 新的API端点提供了更灵活的进度查询方式