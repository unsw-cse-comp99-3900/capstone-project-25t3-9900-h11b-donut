import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .chat_service import AIChatService
from .models import ChatManager, UserStudyPlan

@method_decorator(csrf_exempt, name='dispatch')
class ChatView(View):
  
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def post(self, request):
        """send msg toAI"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({
                    'success': False,
                    'error': 'Message cannot be empty'
                }, status=400)
            
          
            if not hasattr(request, 'account'):
              
                from stu_accounts.models import StudentAccount
                from django.contrib.auth.models import User
                
                # Obtain authentication token from request header (temporarily allow token free access)
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer ') or True:  
                    token = auth_header[7:]  
                    
                    #We should verify the token here and obtain the corresponding user
                    #Temporarily use a simple logic: retrieve the user ID from localStorage
                    #In practical applications, the token should be verified and the corresponding user should be obtained here
                                        
                    #Retrieve user ID from request parameters or request body
                    user_id = request.GET.get('user_id') or data.get('user_id')
                    if not user_id:
                        return JsonResponse({
                            'success': False,
                            'error': 'User ID is required'
                        }, status=400)
                    
                    print(f"[DEBUG] get user's history: user_id={user_id}")
                    
                    account, created = StudentAccount.objects.get_or_create(
                        student_id=user_id,
                        defaults={
                            'name': f'User {user_id}',
                            'email': f'{user_id}@example.com',
                            'password_hash': 'default_password_hash'
                        }
                    )
                    if created:
                        print(f"[DEBUG] create new account: {user_id}")
                    else:
                        print(f"[DEBUG] use available account: {user_id}")
                    
                    request.account = account
                else:
                  
                    return JsonResponse({
                        'success': False,
                        'error': 'Authentication required'
                    }, status=401)
            
            # handle msg and ai response
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
        """get history conversation"""
        try:
          
            if not hasattr(request, 'account'):
               
                from stu_accounts.models import StudentAccount
                from django.contrib.auth.models import User
                
                
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer ') or True: 
                    token = auth_header[7:]  
                    
                    #We should verify the token here and obtain the corresponding user
                    #Temporarily use a simple logic: retrieve the user ID from localStorage
                    #In practical applications, the token should be verified and the corresponding user should be obtained here
                                        
                    #Retrieve user ID from request parameters or request body
                    user_id = request.GET.get('user_id') or data.get('user_id')
                    if not user_id:
                        return JsonResponse({
                            'success': False,
                            'error': 'User ID is required'
                        }, status=400)
                    
                    print(f"[DEBUG] get user's history: user_id={user_id}")
                    
                    account, created = StudentAccount.objects.get_or_create(
                        student_id=user_id,
                        defaults={
                            'name': f'User {user_id}',
                            'email': f'{user_id}@example.com',
                            'password_hash': 'default_password_hash'
                        }
                    )
                    if created:
                        print(f"[DEBUG] create new account: {user_id}")
                    else:
                        print(f"[DEBUG] use available account: {user_id}")
                    
                    request.account = account
                else:
                  
                    return JsonResponse({
                        'success': False,
                        'error': 'Authentication required'
                    }, status=401)
            
            limit = int(request.GET.get('limit', 50))
            days = request.GET.get('days')
            
            # If days are specified, use them directly
            if days:
                history = self.chat_service.get_conversation_history(request.account, limit, int(days))
            else:
                # If days are not specified, first get the number of messages from the last 5 days
                recent_messages = self.chat_service.get_conversation_history(request.account, 200, 5)
                
                # If the number of messages in the last 5 days exceeds 100, only load messages from the last 3 days
                if len(recent_messages) > 100:
                    history = self.chat_service.get_conversation_history(request.account, limit, 3)
                    print(f"[DEBUG] High message count ({len(recent_messages)} messages), loading last 3 days of history")
                else:
                    history = self.chat_service.get_conversation_history(request.account, limit, 5)
                    print(f"[DEBUG] Moderate message count ({len(recent_messages)} messages), loading last 5 days of history")
            
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
    """Study plan storage API view"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def post(self, request):
        """Save study plan data"""
        try:
            # Check authentication, use real user account
            if not hasattr(request, 'account'):
                # Get user ID from request parameters
                user_id = request.GET.get('user_id')
                if not user_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'User ID is required'
                    }, status=400)
                
                print(f"[DEBUG] Saving study plan: user_id={user_id}")
                
                # Create or get corresponding student account
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
                    print(f"[DEBUG] Created new user account: {user_id}")
                else:
                    print(f"[DEBUG] Using existing user account: {user_id}")
                
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
        """Get current study plan"""
        try:
            # Check authentication, use real user account
            if not hasattr(request, 'account'):
                # Get user ID from request parameters
                user_id = request.GET.get('user_id')
                if not user_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'User ID is required'
                    }, status=400)
                
                print(f"[DEBUG] Getting study plan: user_id={user_id}")
                
                # Create or get corresponding student account
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
                    print(f"[DEBUG] Created new user account: {user_id}")
                else:
                    print(f"[DEBUG] Using existing user account: {user_id}")
                
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
    """Data cleanup API view"""
    
    def post(self, request):
        """Clean up old conversation records and plan data"""
        try:
            # Clean up conversation records older than 7 days
            ChatManager.cleanup_old_conversations()
            
            # Clean up study plans older than 7 days
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
    """API to check if greeting message needs to be sent"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def get(self, request):
        """Check if greeting message needs to be sent"""
        try:
            # Check authentication or create temporary account for testing
            if not hasattr(request, 'account'):
                # Temporary solution: create or get test account
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
    """Health check API"""
    
    def get(self, request):
        """Check AI chat service status"""
        return JsonResponse({
            'success': True,
            'status': 'healthy',
            'service': 'AI Chat Service'
        })

@method_decorator(csrf_exempt, name='dispatch')
class GeneratePracticeView(View):
    """Practice generation API"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = AIChatService()
    
    def post(self, request):
        """Generate practice questions"""
        try:
            data = json.loads(request.body)
            course = data.get('course', '').strip()
            topic = data.get('topic', '').strip()
            user_id = data.get('user_id', '').strip()
            num_questions = data.get('num_questions', 5)  # Default 5 questions
            difficulty = data.get('difficulty', 'medium').lower()  # Default medium
            
            if not course or not topic or not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Course, topic, and user_id are required'
                }, status=400)
            
            # Validate number of questions
            try:
                num_questions = int(num_questions)
                if num_questions < 1 or num_questions > 50:
                    num_questions = 5
            except (ValueError, TypeError):
                num_questions = 5
            
            # Validate difficulty
            if difficulty not in ['easy', 'medium', 'hard']:
                difficulty = 'medium'
            
            # Get user account
            from stu_accounts.models import StudentAccount
            try:
                account = StudentAccount.objects.get(student_id=user_id)
            except StudentAccount.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found'
                }, status=404)
            
            # 🔥 Call generator logic directly to avoid HTTP call timeout
            from ai_question_generator.generator import QuestionGenerator
            from courses.models import Question, QuestionChoice, QuestionKeyword, QuestionKeywordMap
            import uuid
            
            print(f"[DEBUG] Starting practice question generation: course={course}, topic={topic}, num={num_questions}, difficulty={difficulty}")
            
            # Get sample questions
            topic_lower = topic.lower()
            
            # Method 1: Find by keyword
            keyword_maps = QuestionKeywordMap.objects.filter(
                keyword__name__icontains=topic_lower
            ).select_related('question')
            
            sample_questions_objs = [km.question for km in keyword_maps if km.question.course_code == course]
            
            # Method 2: If not found, try direct course matching
            if not sample_questions_objs:
                sample_questions_objs = list(Question.objects.filter(
                    course_code=course,
                    is_active=True
                )[:5])
            
            print(f"[DEBUG] Found {len(sample_questions_objs)} sample questions")
            
            # Convert to dictionary format
            sample_questions = []
            for q in sample_questions_objs[:5]:
                q_dict = {
                    'type': q.qtype,
                    'question': q.text,
                    'topic': topic,
                    'difficulty': difficulty,  # Use user-selected difficulty
                    'score': 10
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
                    # Get keywords from keywords_json field
                    if q.keywords_json:
                        q_dict['grading_points'] = q.keywords_json if isinstance(q.keywords_json, list) else []
                    else:
                        q_dict['grading_points'] = []
                
                sample_questions.append(q_dict)
            
            # Calculate MCQ and short answer ratio based on number of questions (60% MCQ, 40% Short Answer)
            mcq_count = int(num_questions * 0.6)
            short_answer_count = num_questions - mcq_count
            
            # Call AI generator
            try:
                generator = QuestionGenerator()
                generated_questions = generator.generate_questions(
                    topic=topic,
                    difficulty=difficulty,  # Use user-selected difficulty
                    sample_questions=sample_questions,
                    count=num_questions,  # Use user-selected count
                    mcq_count=mcq_count,
                    short_answer_count=short_answer_count
                )
                
                print(f"[DEBUG] Generated {len(generated_questions)} questions")
                
                # Save to database
                from ai_question_generator.models import GeneratedQuestion
                session_id = str(uuid.uuid4())
                
                for idx, q in enumerate(generated_questions, 1):
                    # Build question_data JSON
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
                
                # 🔥 Save practice ready message to chat history
                conversation = self.chat_service.get_or_create_conversation(account)
                practice_message_content = f"I've generated {len(generated_questions)} {difficulty} questions for {course} – {topic}. Ready to practice?"
                
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
                print(f"[DEBUG] Practice ready message saved to chat history")
                
                return JsonResponse({
                    'success': True,
                    'session_id': session_id,
                    'total_questions': len(generated_questions),
                    'course': course,
                    'topic': topic
                })
                
            except Exception as gen_error:
                print(f"[DEBUG] Failed to generate questions: {gen_error}")
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