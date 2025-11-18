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
                    
                    # 从请求参数或请求体获取用户ID
                    user_id = request.GET.get('user_id') or data.get('user_id')
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
                            'password_hash': 'default_password_hash'
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
                    
                    # 从请求参数或请求体获取用户ID
                    user_id = request.GET.get('user_id') or data.get('user_id')
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
                            'password_hash': 'default_password_hash'
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

@method_decorator(csrf_exempt, name='dispatch')
class GeneratePracticeView(View):
    """练习生成API"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def post(self, request):
        """生成练习题目"""
        try:
            data = json.loads(request.body)
            course = data.get('course', '').strip()
            topic = data.get('topic', '').strip()
            user_id = data.get('user_id', '').strip()
            
            if not course or not topic or not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Course, topic, and user_id are required'
                }, status=400)
            
            # 获取用户账户
            from stu_accounts.models import StudentAccount
            try:
                account = StudentAccount.objects.get(student_id=user_id)
            except StudentAccount.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found'
                }, status=404)
            
            # 🔥 直接调用生成器逻辑,避免HTTP调用超时
            from ai_question_generator.generator import QuestionGenerator
            from courses.models import Question, QuestionChoice, QuestionKeyword, QuestionKeywordMap
            import uuid
            
            print(f"[DEBUG] 开始生成练习题: course={course}, topic={topic}")
            
            # 获取示例题目
            topic_lower = topic.lower()
            
            # 方法1: 通过关键词查找
            keyword_maps = QuestionKeywordMap.objects.filter(
                keyword__name__icontains=topic_lower
            ).select_related('question')
            
            sample_questions_objs = [km.question for km in keyword_maps if km.question.course_code == course]
            
            # 方法2: 如果没找到,尝试直接匹配课程
            if not sample_questions_objs:
                sample_questions_objs = list(Question.objects.filter(
                    course_code=course,
                    is_active=True
                )[:5])
            
            print(f"[DEBUG] 找到 {len(sample_questions_objs)} 个示例题目")
            
            # 转换为字典格式
            sample_questions = []
            for q in sample_questions_objs[:5]:
                q_dict = {
                    'type': q.qtype,
                    'question': q.text,
                    'topic': topic,
                    'difficulty': 'medium',  # Question模型没有difficulty字段
                    'score': 10  # Question模型没有score字段
                }
                
                if q.qtype == 'mcq':
                    choices = QuestionChoice.objects.filter(question=q)
                    q_dict['options'] = [c.content for c in choices]
                    correct_choice = choices.filter(is_correct=True).first()
                    if correct_choice:
                        q_dict['correct_answer'] = correct_choice.label or 'A'
                    q_dict['explanation'] = q.description or ''
                else:
                    q_dict['sample_answer'] = q.short_answer or ''
                    # 从keywords_json字段获取关键词
                    if q.keywords_json:
                        q_dict['grading_points'] = q.keywords_json if isinstance(q.keywords_json, list) else []
                    else:
                        q_dict['grading_points'] = []
                
                sample_questions.append(q_dict)
            
            # 调用AI生成器
            try:
                generator = QuestionGenerator()
                generated_questions = generator.generate_questions(
                    topic=topic,
                    difficulty='medium',
                    sample_questions=sample_questions,
                    count=5,
                    mcq_count=3,
                    short_answer_count=2
                )
                
                print(f"[DEBUG] 生成了 {len(generated_questions)} 个题目")
                
                # 保存到数据库
                from ai_question_generator.models import GeneratedQuestion
                session_id = str(uuid.uuid4())
                
                for idx, q in enumerate(generated_questions, 1):
                    # 构建question_data JSON
                    question_data = {
                        'question': q.get('question'),
                        'score': q.get('score', 10)
                    }
                    
                    if q.get('type') == 'mcq':
                        question_data.update({
                            'options': q.get('options'),
                            'correct_answer': q.get('correct_answer'),
                            'explanation': q.get('explanation')
                        })
                    else:
                        question_data.update({
                            'sample_answer': q.get('sample_answer'),
                            'grading_points': q.get('grading_points')
                        })
                    
                    GeneratedQuestion.objects.create(
                        session_id=session_id,
                        course_code=course,
                        topic=topic,
                        difficulty=q.get('difficulty', 'medium'),
                        question_type=q.get('type'),
                        question_data=question_data
                    )
                
                # 🔥 保存练习就绪消息到聊天历史
                conversation = self.chat_service.get_or_create_conversation(account)
                practice_message_content = f"I've generated {len(generated_questions)} practice questions for {course} – {topic}. Ready to practice?"
                
                from .models import ChatMessage
                ChatMessage.objects.create(
                    conversation=conversation,
                    message_type='ai',
                    content=practice_message_content,
                    metadata={
                        'messageType': 'practice_ready',
                        'practiceInfo': {
                            'course': course,
                            'topic': topic,
                            'sessionId': session_id,
                            'totalQuestions': len(generated_questions)
                        }
                    }
                )
                print(f"[DEBUG] 已保存练习就绪消息到聊天历史")
                
                return JsonResponse({
                    'success': True,
                    'session_id': session_id,
                    'total_questions': len(generated_questions),
                    'course': course,
                    'topic': topic
                })
                
            except Exception as gen_error:
                print(f"[DEBUG] 生成题目失败: {gen_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to generate questions: {str(gen_error)}'
                }, status=500)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            print(f"[DEBUG] GeneratePracticeView error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)