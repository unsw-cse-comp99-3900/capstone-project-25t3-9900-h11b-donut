# AI Module 集成的 Django Views
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from ai_module.plan_generator import generate_plan

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class GenerateStudyPlanView(View):
    """API View for Generating Learning Plans"""
    
    def post(self, request):
        try:
            # 1. Analyze request data
            data = json.loads(request.body)
            
            # 2. Extract preference settings
            preferences = self._extract_preferences(data.get('preferences', {}))
            
            # 3. Extract task data
            tasks_meta = self._extract_tasks(data.get('tasks', []))
            
            # 4. validation
            if not tasks_meta:
                return JsonResponse({
                    'ok': False,
                    'error': 'No tasks provided'
                }, status=400)
            
            # 5. Call AI module to generate plan
            
            user_timezone = data.get('timezone', 'Australia/Sydney')
            logger.info(f"Generating study plan for user {request.user.id}, timezone: {user_timezone}")
            result = generate_plan(preferences, tasks_meta, user_timezone=user_timezone)

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
        """保存计划到数据库，同时保存到AI对话模块"""
        try:
            # 导入AI对话模块的服务
            from ai_chat.chat_service import AIChatService
            
            # 保存到AI对话模块
            chat_service = AIChatService()
            success = chat_service.save_study_plan(user, plan_data)
            
            if success:
                logger.info(f"Study plan saved to AI chat module for user {user.id}")
            else:
                logger.warning(f"Failed to save plan to AI chat module for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error saving plan to AI chat module for user {user.id}: {str(e)}")
            # 不抛出异常，避免影响主要的计划生成流程

@csrf_exempt
def test_ai_module(request):
    """Simple endpoints for testing AI modules"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    # test data
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
        result = generate_plan(test_preferences, test_tasks, user_timezone='Australia/Sydney')
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class GenerateStudyPlanFromDBView(View):
    """Retrieve data from the database and generate a learning plan"""
    
    def post(self, request):
        try:

            tasks_meta = self._get_user_tasks_from_db(request.user)
            
            preferences = self._get_user_preferences_from_db(request.user)
            
            user_timezone = body.get('timezone', 'Australia/Sydney') 
            result = generate_plan(preferences, tasks_meta, user_timezone=user_timezone)

            if result.get('ok'):
                self._save_plan_to_database(request.user, result)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error generating study plan from DB for user {request.user.id}: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _get_user_tasks_from_db(self, user):
        """Retrieve data from the database and generate a learning plan"""
        # TODO: 
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
        """Retrieve user preferences from the database"""
        # TODO: 
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
        """Save the plan to the database and also save it to the AI dialogue module"""
        try:
            # Importing AI dialogue module services
            from ai_chat.chat_service import AIChatService
            
            # Save to AI dialogue module
            chat_service = AIChatService()
            success = chat_service.save_study_plan(user, plan_data)
            
            if success:
                logger.info(f"Study plan saved to AI chat module for user {user.id}")
            else:
                logger.warning(f"Failed to save plan to AI chat module for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error saving plan to AI chat module for user {user.id}: {str(e)}")