# AI Module 集成的 Django Views
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

# 导入你的AI模块
from ai_module.plan_generator import generate_plan

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class GenerateStudyPlanView(View):
    """生成学习计划的API视图"""
    
    def post(self, request):
        try:
            # 1. 解析请求数据
            data = json.loads(request.body)
            
            # 2. 提取偏好设置
            preferences = self._extract_preferences(data.get('preferences', {}))
            
            # 3. 提取任务数据
            tasks_meta = self._extract_tasks(data.get('tasks', []))
            
            # 4. 验证数据
            if not tasks_meta:
                return JsonResponse({
                    'ok': False,
                    'error': 'No tasks provided'
                }, status=400)
            
            # 5. 调用AI模块生成计划
            logger.info(f"Generating study plan for user {request.user.id}")
            result = generate_plan(preferences, tasks_meta)
            
            # 6. 可选：保存到数据库
            if result.get('ok'):
                self._save_plan_to_database(request.user, result)
                logger.info(f"Study plan generated successfully for user {request.user.id}")
            else:
                logger.warning(f"Study plan generation failed for user {request.user.id}: {result.get('message', 'Unknown error')}")
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error generating study plan for user {request.user.id}: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _extract_preferences(self, prefs_data):
        """提取和验证偏好设置"""
        return {
            'daily_hour_cap': int(prefs_data.get('daily_hour_cap', 3)),
            'weekly_study_days': int(prefs_data.get('weekly_study_days', 5)),
            'avoid_days': prefs_data.get('avoid_days', [5, 6])  # 默认避开周末
        }
    
    def _extract_tasks(self, tasks_data):
        """提取和验证任务数据"""
        tasks_meta = []
        for task in tasks_data:
            if all(key in task for key in ['id', 'task', 'dueDate']):
                tasks_meta.append({
                    'id': str(task['id']),
                    'task': str(task['task']),
                    'dueDate': str(task['dueDate']),
                    'detailPdfPath': task.get('detailPdfPath'),
                    'estimatedHours': task.get('estimatedHours')
                })
        return tasks_meta
    
    def _save_plan_to_database(self, user, plan_data):
        """保存计划到数据库（需要根据你的模型实现）"""
        # TODO: 实现数据库保存逻辑
        # 示例：
        # StudyPlan.objects.create(user=user, plan_data=plan_data)
        pass

@csrf_exempt
def test_ai_module(request):
    """测试AI模块的简单端点"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    # 使用测试数据
    test_preferences = {
        'daily_hour_cap': 3,
        'weekly_study_days': 5,
        'avoid_days': [5, 6]
    }
    
    test_tasks = [
        {
            'id': '9517_a1',
            'task': 'COMP9517 - Assignment 1',
            'dueDate': '2025-10-25',
            'detailPdfPath': 'ai_module/9517assignment1.pdf'
        },
        {
            'id': '9900_a1',
            'task': 'COMP9900 - Assignment 1', 
            'dueDate': '2025-10-30',
            'detailPdfPath': 'ai_module/9900assignment1.pdf'
        }
    ]
    
    try:
        result = generate_plan(test_preferences, test_tasks)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# 如果你需要从数据库获取数据的版本
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class GenerateStudyPlanFromDBView(View):
    """从数据库获取数据并生成学习计划"""
    
    def post(self, request):
        try:
            # 1. 从数据库获取用户的课程和作业
            tasks_meta = self._get_user_tasks_from_db(request.user)
            
            # 2. 从数据库获取用户偏好
            preferences = self._get_user_preferences_from_db(request.user)
            
            # 3. 调用AI模块
            result = generate_plan(preferences, tasks_meta)
            
            # 4. 保存结果
            if result.get('ok'):
                self._save_plan_to_database(request.user, result)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error generating study plan from DB for user {request.user.id}: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _get_user_tasks_from_db(self, user):
        """从数据库获取用户的任务列表"""
        # TODO: 根据你的数据模型实现
        # 示例：
        # tasks = []
        # user_courses = Course.objects.filter(students=user)
        # for course in user_courses:
        #     for assignment in course.assignments.all():
        #         tasks.append({
        #             'id': f"{course.code}_{assignment.id}",
        #             'task': f"{course.code} - {assignment.title}",
        #             'dueDate': assignment.due_date.isoformat(),
        #             'detailPdfPath': assignment.pdf_file.path if assignment.pdf_file else None
        #         })
        # return tasks
        return []
    
    def _get_user_preferences_from_db(self, user):
        """从数据库获取用户偏好"""
        # TODO: 根据你的数据模型实现
        # 示例：
        # try:
        #     prefs = UserPreference.objects.get(user=user)
        #     return {
        #         'daily_hour_cap': prefs.daily_hours,
        #         'weekly_study_days': prefs.weekly_days,
        #         'avoid_days': prefs.avoid_days
        #     }
        # except UserPreference.DoesNotExist:
        #     return {'daily_hour_cap': 3, 'weekly_study_days': 5, 'avoid_days': [5, 6]}
        return {'daily_hour_cap': 3, 'weekly_study_days': 5, 'avoid_days': [5, 6]}
    
    def _save_plan_to_database(self, user, plan_data):
        """保存计划到数据库"""
        # TODO: 实现保存逻辑
        pass