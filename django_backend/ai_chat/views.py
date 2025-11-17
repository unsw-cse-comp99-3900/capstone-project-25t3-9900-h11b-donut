import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .chat_service import AIChatService
from .models import ChatManager, UserStudyPlan

@method_decorator(csrf_exempt, name='dispatch')
class ChatView(View):
    """AI对话API视图"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def post(self, request):
        """发送消息到AI"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({
                    'success': False,
                    'error': 'Message cannot be empty'
                }, status=400)
            
            # 检查认证，使用真实的用户账户
            if not hasattr(request, 'account'):
                # 尝试从认证token获取真实用户
                from stu_accounts.models import StudentAccount
                from django.contrib.auth.models import User
                
                # 从请求头获取认证token（暂时允许无token访问）
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer ') or True:  # 暂时允许无token访问
                    token = auth_header[7:]  # 去掉'Bearer '前缀
                    
                    # 这里应该验证token并获取对应的用户
                    # 暂时使用一个简单的逻辑：从localStorage中获取用户ID
                    # 在实际应用中，这里应该验证token并获取对应的用户
                    
                    # 从请求参数获取用户ID
                    user_id = request.GET.get('user_id')
                    if not user_id:
                        return JsonResponse({
                            'success': False,
                            'error': 'User ID is required'
                        }, status=400)
                    
                    print(f"[DEBUG] 获取用户历史: user_id={user_id}")
                    
                    # 创建或获取对应的学生账户
                    account, created = StudentAccount.objects.get_or_create(
                        student_id=user_id,
                        defaults={
                            'name': f'User {user_id}',
                            'email': f'{user_id}@example.com',
                            'password': 'default_password'
                        }
                    )
                    if created:
                        print(f"[DEBUG] 创建新用户账户: {user_id}")
                    else:
                        print(f"[DEBUG] 使用现有用户账户: {user_id}")
                    
                    request.account = account
                else:
                    # 如果没有认证信息，返回错误
                    return JsonResponse({
                        'success': False,
                        'error': 'Authentication required'
                    }, status=401)
            
            # 处理消息并获取AI回复
            result = self.chat_service.process_message(request.account, message)
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        """获取对话历史"""
        try:
            # 检查认证，使用真实的用户账户
            if not hasattr(request, 'account'):
                # 尝试从认证token获取真实用户
                from stu_accounts.models import StudentAccount
                from django.contrib.auth.models import User
                
                # 从请求头获取认证token（暂时允许无token访问）
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer ') or True:  # 暂时允许无token访问
                    token = auth_header[7:]  # 去掉'Bearer '前缀
                    
                    # 这里应该验证token并获取对应的用户
                    # 暂时使用一个简单的逻辑：从localStorage中获取用户ID
                    # 在实际应用中，这里应该验证token并获取对应的用户
                    
                    # 从请求参数获取用户ID
                    user_id = request.GET.get('user_id')
                    if not user_id:
                        return JsonResponse({
                            'success': False,
                            'error': 'User ID is required'
                        }, status=400)
                    
                    print(f"[DEBUG] 获取用户历史: user_id={user_id}")
                    
                    # 创建或获取对应的学生账户
                    account, created = StudentAccount.objects.get_or_create(
                        student_id=user_id,
                        defaults={
                            'name': f'User {user_id}',
                            'email': f'{user_id}@example.com',
                            'password': 'default_password'
                        }
                    )
                    if created:
                        print(f"[DEBUG] 创建新用户账户: {user_id}")
                    else:
                        print(f"[DEBUG] 使用现有用户账户: {user_id}")
                    
                    request.account = account
                else:
                    # 如果没有认证信息，返回错误
                    return JsonResponse({
                        'success': False,
                        'error': 'Authentication required'
                    }, status=401)
            
            limit = int(request.GET.get('limit', 50))
            days = request.GET.get('days')
            
            # 如果指定了天数，直接使用
            if days:
                history = self.chat_service.get_conversation_history(request.account, limit, int(days))
            else:
                # 如果没有指定天数，先获取最近5天的消息数量
                recent_messages = self.chat_service.get_conversation_history(request.account, 200, 5)
                
                # 如果最近5天的消息数量超过100条，则只加载最近3天的消息
                if len(recent_messages) > 100:
                    history = self.chat_service.get_conversation_history(request.account, limit, 3)
                    print(f"[DEBUG] 消息数量较多 ({len(recent_messages)}条)，加载最近3天的历史")
                else:
                    history = self.chat_service.get_conversation_history(request.account, limit, 5)
                    print(f"[DEBUG] 消息数量适中 ({len(recent_messages)}条)，加载最近5天的历史")
            
            return JsonResponse({
                'success': True,
                'messages': history
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StudyPlanView(View):
    """学习计划存储API视图"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def post(self, request):
        """保存学习计划数据"""
        try:
            # 检查认证，使用真实的用户账户
            if not hasattr(request, 'account'):
                # 从请求参数获取用户ID
                user_id = request.GET.get('user_id')
                if not user_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'User ID is required'
                    }, status=400)
                
                print(f"[DEBUG] 保存学习计划: user_id={user_id}")
                
                # 创建或获取对应的学生账户
                from stu_accounts.models import StudentAccount
                account, created = StudentAccount.objects.get_or_create(
                    student_id=user_id,
                    defaults={
                        'name': f'User {user_id}',
                        'email': f'{user_id}@example.com',
                        'password': 'default_password'
                    }
                )
                if created:
                    print(f"[DEBUG] 创建新用户账户: {user_id}")
                else:
                    print(f"[DEBUG] 使用现有用户账户: {user_id}")
                
                request.account = account
            
            data = json.loads(request.body)
            plan_data = data.get('plan_data')
            
            if not plan_data:
                return JsonResponse({
                    'success': False,
                    'error': 'Plan data is required'
                }, status=400)
            
            success = self.chat_service.save_study_plan(request.account, plan_data)
            
            return JsonResponse({
                'success': success,
                'message': 'Study plan saved successfully' if success else 'Failed to save study plan'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        """获取当前学习计划"""
        try:
            # 检查认证，使用真实的用户账户
            if not hasattr(request, 'account'):
                # 从请求参数获取用户ID
                user_id = request.GET.get('user_id')
                if not user_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'User ID is required'
                    }, status=400)
                
                print(f"[DEBUG] 获取学习计划: user_id={user_id}")
                
                # 创建或获取对应的学生账户
                from stu_accounts.models import StudentAccount
                account, created = StudentAccount.objects.get_or_create(
                    student_id=user_id,
                    defaults={
                        'name': f'User {user_id}',
                        'email': f'{user_id}@example.com',
                        'password': 'default_password'
                    }
                )
                if created:
                    print(f"[DEBUG] 创建新用户账户: {user_id}")
                else:
                    print(f"[DEBUG] 使用现有用户账户: {user_id}")
                
                request.account = account
            
            plan_data = self.chat_service.get_user_study_plan(request.account)
            
            return JsonResponse({
                'success': True,
                'plan_data': plan_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CleanupView(View):
    """数据清理API视图"""
    
    def post(self, request):
        """清理旧的对话记录和计划数据"""
        try:
            # 清理7天前的对话记录
            ChatManager.cleanup_old_conversations()
            
            # 清理7天前的学习计划
            UserStudyPlan.cleanup_old_plans()
            
            return JsonResponse({
                'success': True,
                'message': 'Old data cleaned up successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GreetingCheckView(View):
    """检查是否需要发送问候消息的API"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def get(self, request):
        """检查是否需要发送问候消息"""
        try:
            # 检查认证或创建临时账户用于测试
            if not hasattr(request, 'account'):
                # 临时解决方案：创建或获取测试账户
                from stu_accounts.models import StudentAccount
                test_account, created = StudentAccount.objects.get_or_create(
                    student_id='test_student',
                    defaults={
                        'name': 'Test Student',
                        'email': 'test@example.com',
                        'password': 'test_password'
                    }
                )
                request.account = test_account
            
            should_greet = self.chat_service.should_send_greeting(request.account)
            
            return JsonResponse({
                'success': True,
                'should_send_greeting': should_greet
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """健康检查API"""
    
    def get(self, request):
        """检查AI对话服务状态"""
        return JsonResponse({
            'success': True,
            'status': 'healthy',
            'service': 'AI Chat Service'
        })