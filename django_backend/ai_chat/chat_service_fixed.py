import json
import re
import os
import importlib
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User
from stu_accounts.models import StudentAccount
from .models import ChatConversation, ChatMessage, UserStudyPlan
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
use_gemini: bool = bool(GEMINI_KEY)
genai: Any = None

if use_gemini:
    try:
        genai = importlib.import_module("google.generativeai")
        genai.configure(api_key=GEMINI_KEY)
        _model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"temperature": 0.7, "max_output_tokens": 1024}
        )
    except Exception as e:
        print(f"[DEBUG] Gemini 初始化失败: {e}")
        use_gemini = False

class AIChatService:
    """AI聊天服务 - 简化版本"""
    
    def __init__(self):
        pass
    
    def detect_intent(self, message: str) -> str:
        """检测用户意图"""
        message_lower = message.lower()
        
        # 解释计划意图
        if any(keyword in message_lower for keyword in [
            'explain my plan', 'explain plan', 'tell me about my plan',
            'what is my plan', 'describe my plan', 'plan explanation'
        ]):
            return 'explain_plan'
        
        # 其他情况都返回通用意图
        return 'general'
    
    def get_user_study_plan(self, account: StudentAccount) -> Optional[Dict]:
        """获取用户的当前学习计划"""
        try:
            # 创建临时User对象用于查询
            user, _ = User.objects.get_or_create(
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()
            return plan.plan_data if plan else None
        except Exception:
            return None
    
    def generate_plan_explanation(self, account: StudentAccount) -> str:
        """生成学习计划解释"""
        plan_data = self.get_user_study_plan(account)
        
        if not plan_data:
            return """
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    I don't see an active study plan for you yet. 📋
                </div>
                <div style="line-height: 1.6;">
                    To get a personalized explanation, please generate your study plan first from the "My Plan" section.
                    <br /><br />
                    Once you have a plan, I can explain:
                    <ul style="padding-left: 18px; margin: '8px 0';">
                        <li>How your plan was created based on your preferences</li>
                        <li>Why tasks are scheduled in a specific order</li>
                        <li>How deadlines and workload are balanced</li>
                        <li>Tips for following your personalized schedule</li>
                    </ul>
                </div>
            </div>
            """
        
        # 提取计划信息
        ai_summary = plan_data.get('aiSummary', {})
        description = ai_summary.get('description', '')
        tasks = ai_summary.get('tasks', [])
        
        # 如果有保存的描述，使用它
        if description:
            return f"""
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    Here's the explanation of your personalized study plan: ✨
                </div>
                <div style="line-height: 1.6;">
                    {description}
                    <br /><br />
                    Your plan includes <strong>{len(tasks)} tasks</strong> designed to help you achieve your learning goals efficiently.
                </div>
            </div>
            """
        
        # 如果没有描述，生成基本解释
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Here's your personalized study plan overview: 📚
            </div>
            <div style="line-height: 1.6;">
                Your plan has been carefully designed with <strong>{len(tasks)} tasks</strong> to help you achieve your learning objectives.
                <br /><br />
                The plan takes into account your schedule, preferences, and learning goals to create an optimal study path.
                Each task is structured to build upon previous knowledge and prepare you for upcoming challenges.
            </div>
        </div>
        """
    
    def generate_welcome_response(self) -> str:
        """生成固定的欢迎回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Hello! 👋 I'm your AI Learning Coach.
            </div>
            <div style="line-height: 1.6;">
                I'd love to help you with that! 🤔
                <br /><br />
                To give you the best assistance, could you tell me a bit more about what you're working on?
                <br /><br />
                You can ask me about:
                <ul style="padding-left: 18px; margin: '8px 0';">
                    <li>Your study plan and schedule</li>
                    <li>Specific tasks or assignments</li>
                    <li>Practice exercises for difficult topics</li>
                    <li>Or just ask for some encouragement!</li>
                </ul>
            </div>
        </div>
        """
    
    def generate_ai_response(self, message: str, account: StudentAccount, conversation_history: List[Dict] = None) -> str:
        """生成AI回复 - 简化版本"""
        # 检测用户意图
        intent = self.detect_intent(message)
        
        # 如果用户要求解释计划，返回保存的计划描述
        if intent == 'explain_plan':
            return self.generate_plan_explanation(account)
        
        # 对于其他所有情况，返回固定的欢迎回复
        return self.generate_welcome_response()
    
    def get_or_create_conversation(self, account: StudentAccount) -> ChatConversation:
        """获取或创建对话会话"""
        # 创建或获取User对象
        user, _ = User.objects.get_or_create(
            username=account.student_id,
            defaults={'email': account.email or f'{account.student_id}@temp.com'}
        )
        
        # 获取或创建对话会话
        conversation, created = ChatConversation.objects.get_or_create(
            user=user,
            defaults={'is_active': True}
        )
        return conversation
    
    def get_conversation_history(self, account: StudentAccount, limit: int = 50) -> List[Dict]:
        """获取对话历史"""
        try:
            conversation = self.get_or_create_conversation(account)
            messages = ChatMessage.objects.filter(
                conversation=conversation
            ).order_by('-timestamp')[:limit]
            
            # 转换为前端需要的格式
            history = []
            for msg in reversed(messages):
                history.append({
                    'id': msg.id,
                    'type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata or {}
                })
            
            return history
        except Exception as e:
            print(f"[DEBUG] 获取对话历史失败: {e}")
            return []
    
    def process_message(self, account: StudentAccount, message: str) -> Dict[str, Any]:
        """处理用户消息并生成AI回复"""
        try:
            # 获取或创建对话会话
            conversation = self.get_or_create_conversation(account)
            
            # 获取对话历史用于上下文
            conversation_history = self.get_conversation_history(account, limit=10)
            
            # 保存用户消息
            user_message = ChatMessage.objects.create(
                conversation=conversation,
                message_type='user',
                content=message
            )
            
            # 生成AI回复
            ai_response = self.generate_ai_response(message, account, conversation_history)
            
            # 检测意图（用于元数据）
            intent = self.detect_intent(message)
            
            # 保存AI回复
            ai_message = ChatMessage.objects.create(
                conversation=conversation,
                message_type='ai',
                content=ai_response,
                metadata={'intent': intent, 'ai_powered': use_gemini}
            )
            
            return {
                'success': True,
                'user_message': {
                    'id': user_message.id,
                    'content': user_message.content,
                    'timestamp': user_message.timestamp.isoformat(),
                    'type': 'user'
                },
                'ai_response': {
                    'id': ai_message.id,
                    'content': ai_message.content,
                    'timestamp': ai_message.timestamp.isoformat(),
                    'type': 'ai',
                    'intent': intent,
                    'ai_powered': use_gemini
                }
            }
            
        except Exception as e:
            print(f"[DEBUG] 消息处理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_study_plan(self, account: StudentAccount, plan_data: Dict) -> bool:
        """保存学习计划数据"""
        try:
            # 创建临时User对象
            user, _ = User.objects.get_or_create(
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            
            # 停用旧的计划
            UserStudyPlan.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # 创建新的活跃计划
            UserStudyPlan.objects.create(
                user=user,
                plan_data=plan_data,
                is_active=True
            )
            
            return True
        except Exception:
            return False