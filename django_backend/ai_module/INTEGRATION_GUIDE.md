# AI Module Django 集成指南

## 概述
如何将 ai_module 与 Django 后端完整集成，处理真实的课程数据和学生偏好。

## 1. Django API 端点创建

### 创建 API Views
```python
# django_backend/api/views.py (或相应的views文件)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from ai_module.plan_generator import generate_plan

@csrf_exempt
@login_required
def generate_study_plan(request):
    """
    生成学习计划的API端点
    POST /api/generate-study-plan/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # 1. 解析前端请求数据
        data = json.loads(request.body)
        
        # 2. 获取学生偏好
        preferences = data.get('preferences', {})
        # 确保有默认值
        preferences = {
            'daily_hour_cap': preferences.get('daily_hour_cap', 3),
            'weekly_study_days': preferences.get('weekly_study_days', 5),
            'avoid_days': preferences.get('avoid_days', [5, 6])  # 默认避开周末
        }
        
        # 3. 获取任务数据
        tasks_meta = data.get('tasks', [])
        
        # 4. 调用 ai_module
        result = generate_plan(preferences, tasks_meta)
        
        # 5. 可选：保存到数据库
        if result.get('ok'):
            save_study_plan_to_db(request.user, result)
        
        # 6. 返回结果
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def save_study_plan_to_db(user, plan_data):
    """保存生成的计划到数据库（可选）"""
    # 这里实现数据库保存逻辑
    pass
```

### URL 配置
```python
# django_backend/urls.py 或 api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/generate-study-plan/', views.generate_study_plan, name='generate_study_plan'),
    # 其他URL...
]
```

## 2. 前端调用方式

### JavaScript/React 调用示例
```javascript
// 前端调用示例
const generateStudyPlan = async () => {
    const requestData = {
        preferences: {
            daily_hour_cap: 3,
            weekly_study_days: 5,
            avoid_days: [5, 6]  // 周六周日
        },
        tasks: [
            {
                id: "9517_a1",
                task: "COMP9517 - Assignment 1",
                dueDate: "2025-10-25",
                detailPdfPath: "/path/to/pdf/9517assignment1.pdf"
            },
            {
                id: "9900_a1", 
                task: "COMP9900 - Assignment 1",
                dueDate: "2025-10-30",
                detailPdfPath: "/path/to/pdf/9900assignment1.pdf"
            }
            // 更多任务...
        ]
    };

    try {
        const response = await fetch('/api/generate-study-plan/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(), // Django CSRF token
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();
        
        if (result.ok) {
            console.log('生成的学习计划:', result);
            // 处理成功结果
            displayStudyPlan(result);
        } else {
            console.error('计划生成失败:', result.message);
        }
    } catch (error) {
        console.error('API调用失败:', error);
    }
};
```

## 3. 数据库集成（可选）

### Django Models 示例
```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_data = models.JSONField()  # 存储完整的AI生成数据
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class TaskBlock(models.Model):
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=100)
    part_id = models.CharField(max_length=100)
    date = models.DateField()
    title = models.CharField(max_length=200)
    minutes = models.IntegerField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

def save_study_plan_to_db(user, plan_data):
    """保存计划到数据库的具体实现"""
    # 创建主计划记录
    study_plan = StudyPlan.objects.create(
        user=user,
        plan_data=plan_data
    )
    
    # 保存每个任务块用于进度跟踪
    for day in plan_data.get('days', []):
        for block in day.get('blocks', []):
            TaskBlock.objects.create(
                study_plan=study_plan,
                task_id=block['taskId'],
                part_id=block['partId'],
                date=day['date'],
                title=block['title'],
                minutes=block['minutes']
            )
    
    return study_plan
```

## 4. 从数据库获取课程数据

### 如果课程数据存储在数据库中
```python
# views.py 中的完整实现
@csrf_exempt
@login_required
def generate_study_plan_from_db(request):
    """从数据库获取课程数据并生成计划"""
    try:
        # 1. 从数据库获取用户的课程和作业
        user_courses = get_user_courses(request.user)
        tasks_meta = []
        
        for course in user_courses:
            for assignment in course.assignments.all():
                tasks_meta.append({
                    'id': f"{course.code}_{assignment.id}",
                    'task': f"{course.code} - {assignment.title}",
                    'dueDate': assignment.due_date.isoformat(),
                    'detailPdfPath': assignment.pdf_file.path if assignment.pdf_file else None
                })
        
        # 2. 获取用户偏好
        user_prefs = get_user_preferences(request.user)
        preferences = {
            'daily_hour_cap': user_prefs.daily_hours,
            'weekly_study_days': user_prefs.weekly_days,
            'avoid_days': user_prefs.avoid_days
        }
        
        # 3. 调用 ai_module
        result = generate_plan(preferences, tasks_meta)
        
        # 4. 保存结果
        if result.get('ok'):
            save_study_plan_to_db(request.user, result)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_user_courses(user):
    """获取用户的课程（需要根据你的数据模型实现）"""
    # 示例实现
    from courses.models import Course
    return Course.objects.filter(students=user)

def get_user_preferences(user):
    """获取用户偏好（需要根据你的数据模型实现）"""
    # 示例实现
    from preferences.models import UserPreference
    prefs, created = UserPreference.objects.get_or_create(
        user=user,
        defaults={
            'daily_hours': 3,
            'weekly_days': 5,
            'avoid_days': [5, 6]
        }
    )
    return prefs
```

## 5. 测试集成

### 创建测试端点
```python
# views.py
@csrf_exempt
def test_ai_module(request):
    """测试AI模块的端点"""
    # 使用你现有的测试数据
    from ai_module.text_run import tasks_meta, preferences
    
    result = generate_plan(preferences, tasks_meta)
    return JsonResponse(result)
```

### 测试URL
```python
# urls.py
urlpatterns = [
    path('api/test-ai-module/', views.test_ai_module, name='test_ai_module'),
]
```

## 6. 部署注意事项

### PDF文件路径处理
```python
import os
from django.conf import settings

def get_pdf_absolute_path(relative_path):
    """获取PDF文件的绝对路径"""
    if relative_path.startswith('/'):
        return relative_path
    return os.path.join(settings.MEDIA_ROOT, relative_path)

# 在处理tasks_meta时使用
for task in tasks_meta:
    if task.get('detailPdfPath'):
        task['detailPdfPath'] = get_pdf_absolute_path(task['detailPdfPath'])
```

### 环境变量配置
```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API配置
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 确保ai_module能访问到
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
```

## 7. 完整的调用流程示例

```python
# 完整的Django view示例
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from ai_module.plan_generator import generate_plan

@csrf_exempt
@login_required
def generate_complete_study_plan(request):
    """完整的学习计划生成API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # 解析请求数据或从数据库获取
        if request.body:
            # 前端传递数据
            data = json.loads(request.body)
            preferences = data.get('preferences', {})
            tasks_meta = data.get('tasks', [])
        else:
            # 从数据库获取
            preferences = get_user_preferences_dict(request.user)
            tasks_meta = get_user_tasks_list(request.user)
        
        # 调用AI模块
        result = generate_plan(preferences, tasks_meta)
        
        # 保存到数据库
        if result.get('ok'):
            save_study_plan_to_db(request.user, result)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

这样你的ai_module就完全集成到Django后端了！前端只需要调用Django API，不需要直接接触ai_module。