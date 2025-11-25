import json
import re
import os
import importlib
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User
from stu_accounts.models import StudentAccount
from .models import ChatConversation, ChatMessage, UserStudyPlan
from dotenv import load_dotenv

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
        print(f"[DEBUG] Gemini fail to initialize: {e}")
        use_gemini = False

class AIChatService:
    """AI chat - simplified version"""
    
    def __init__(self):
        pass
    
    def detect_intent(self, message: str) -> str:
        """check user's intent"""
        message_lower = message.lower()
        
        # explain intent
        if any(keyword in message_lower for keyword in [
            'explain my plan', 'explain plan', 'tell me about my plan',
            'what is my plan', 'describe my plan', 'plan explanation'
        ]):
            return 'explain_plan'
        
        return 'general'
    
    def get_user_study_plan(self, account: StudentAccount) -> Optional[Dict]:
        """get current plan"""
        try:
            
            user, _ = User.objects.get_or_create(
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()
            return plan.plan_data if plan else None
        except Exception:
            return None
    
    def generate_plan_explanation(self, account: StudentAccount) -> str:
        """explain the plan"""
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
        
        # get plan info/summary
        ai_summary = plan_data.get('aiSummary', {})
        description = ai_summary.get('description', '')
        tasks = ai_summary.get('tasks', [])
        
        # use description if exists
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
        
        # use basic explanation else
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
        """fixed welcome reply"""
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
        """ai response - simplified version"""
        # check intent
        intent = self.detect_intent(message)
        
        # If the user requests an explanation of the plan, return the saved plan description
        if intent == 'explain_plan':
            return self.generate_plan_explanation(account)
        
        # For all other situations, return a fixed welcome reply
        return self.generate_welcome_response()
    
    def get_or_create_conversation(self, account: StudentAccount) -> ChatConversation:
        """Get or create a conversation session"""
        conversation, created = ChatConversation.objects.get_or_create(
            student_id=account.student_id,
            defaults={'student_name': account.name or 'Student'}
        )
        return conversation
    
    def get_conversation_history(self, account: StudentAccount, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        try:
            conversation = self.get_or_create_conversation(account)
            messages = ChatMessage.objects.filter(
                conversation=conversation
            ).order_by('-timestamp')[:limit]
            
            # Convert to the format required by the frontend
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
            print(f"[DEBUG] fail to load history conversation: {e}")
            return []
    
    def process_message(self, account: StudentAccount, message: str) -> Dict[str, Any]:
        """Process user messages and generate AI replies"""
        try:
            # Get or create a conversation session
            conversation = self.get_or_create_conversation(account)
            
            # Retrieve conversation history for context
            conversation_history = self.get_conversation_history(account, limit=10)
            
            # Save user messages
            user_message = ChatMessage.objects.create(
                conversation=conversation,
                message_type='user',
                content=message
            )
            
            # Generate AI reply
            ai_response = self.generate_ai_response(message, account, conversation_history)
            
            # Detecting intent (for metadata)
            intent = self.detect_intent(message)
            
            # Save AI reply
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
            print(f"[DEBUG] fail to handle msg: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_study_plan(self, account: StudentAccount, plan_data: Dict) -> bool:
        """save plan"""
        try:
         
            user, _ = User.objects.get_or_create(
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            
        
            UserStudyPlan.objects.filter(user=user, is_active=True).update(is_active=False)
            
          
            UserStudyPlan.objects.create(
                user=user,
                plan_data=plan_data,
                is_active=True
            )
            
            return True
        except Exception:
            return False