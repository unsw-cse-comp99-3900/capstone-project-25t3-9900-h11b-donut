# pyright: reportAttributeAccessIssue=false
# pyright: reportImplicitRelativeImport=false
import re
import os
import importlib
from typing import Any, Optional
from django.contrib.auth.models import User  # type: ignore
from stu_accounts.models import StudentAccount  # type: ignore
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
    """AI对话服务 - 处理用户消息并生成智能回复"""
    
    def __init__(self):
        self.intent_patterns = {
            'explain_plan': [
                r'explain.*plan', r'plan.*explain', r'tell.*about.*plan',
                r'how.*plan.*work', r'plan.*detail', r'plan.*reason'
            ],
            'task_help': [
                r'part.*\d+', r'task.*approach', r'how.*do.*part',
                r'help.*with.*task', r'task.*detail', r'assignment.*help'
            ],
            'encouragement': [
                r'encourage', r'motivation', r'feel.*bad', r'difficult',
                r'hard.*time', r'struggling', r'anxious', r'worried'
            ],
            'practice': [
                r'practice', r'weak.*topic', r'difficult.*topic',
                r'need.*help.*with', r'don.*understand'
            ],
            'greeting': [
                r'^(hi|hello|hey)', r'good.*morning', r'good.*afternoon'
            ]
        }
    
    def get_or_create_conversation(self, account: StudentAccount) -> ChatConversation:
        """获取或创建用户的对话会话"""
        # 创建或获取一个临时User对象用于兼容现有模型
        user, _ = User.objects.get_or_create(  # type: ignore
            username=account.student_id,
            defaults={'email': account.email or f'{account.student_id}@temp.com'}
        )
        
        conversation, created = ChatConversation.objects.get_or_create(  # type: ignore
            user=user,
            is_active=True,
            defaults={'user': user}
        )
        return conversation
    
    def should_send_greeting(self, account: StudentAccount) -> bool:
        """检查是否应该发送问候消息（现在由前端基于会话管理）"""
        # 由于问候逻辑现在完全由前端管理，这个方法可以返回固定值
        # 或者可以完全移除这个方法，让前端直接决定
        return False  # 前端现在基于会话状态决定是否发送问候
    
    def detect_intent(self, message: str) -> str:
        """检测用户消息的意图"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return 'general'
    
    def get_user_study_plan(self, account: StudentAccount) -> Optional[dict[str, Any]]:
        """获取用户的当前学习计划"""
        try:
            # 创建临时User对象用于查询
            user, _ = User.objects.get_or_create(  # type: ignore
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()  # type: ignore
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

                        <li>Why tasks are scheduled in a specific order</li>
                        <li>How deadlines and workload are balanced</li>
                        <li>Tips for following your personalized schedule</li>
                    </ul>
                </div>
            </div>
            """
        
        # 提取计划信息
        ai_summary = plan_data.get('aiSummary', {})
        tasks = ai_summary.get('tasks', [])
        
        # 构建解释内容
        explanation_parts = []
        
        # 总体说明
        explanation_parts.append("""
            <div style="font-weight: 700; margin-bottom: 8px;">
                Hi! Here's a detailed explanation of your personalized learning plan. ✨
            </div>
        """)
        
        # 计划创建逻辑
        explanation_parts.append("""
            <div style="font-weight: 600; margin-bottom: 4px;">How your plan was created:</div>
            <ul style="padding-left: 18px; margin: 0;">
                <li><strong>Course analysis:</strong> AI analyzed all your course requirements and deadlines</li>
                <li><strong>Task breakdown:</strong> Each assignment was intelligently split into manageable parts</li>
                <li><strong>Time allocation:</strong> Hours distributed based on task complexity and your preferences</li>
                <li><strong>Schedule optimization:</strong> Tasks arranged to avoid conflicts and maintain steady progress</li>
            </ul>
        """)
        
        # 任务详情
        if tasks:
            explanation_parts.append(f"""
                <div style="font-weight: 600; margin: 12px 0 4px;">Your plan includes {len(tasks)} main tasks:</div>
                <ul style="padding-left: 18px; margin: 0;">
            """)
            
            for task in tasks[:3]:  # 只显示前3个任务避免过长
                task_title = task.get('taskTitle', 'Unknown Task')
                parts_count = len(task.get('parts', []))
                total_minutes = task.get('totalMinutes', 0)
                hours = total_minutes // 60
                
                explanation_parts.append(f"""
                    <li><strong>{task_title}:</strong> {parts_count} parts, ~{hours} hours total</li>
                """)
            
            if len(tasks) > 3:
                explanation_parts.append(f"<li><em>...and {len(tasks) - 3} more tasks</em></li>")
            
            explanation_parts.append("</ul>")
        
        # 使用提示
        explanation_parts.append("""
            <div style="margin-top: 12px; padding: 10px; background: '#f8f9fa'; border-radius: 8px;">
                <div style="font-weight: 600; margin-bottom: 4px;">💡 Pro Tips:</div>
                <div>
                    • Your plan automatically adapts if you miss a day<br/>
                    • Each task is broken into focused work sessions<br/>
                    • Ask me about specific parts for detailed guidance!
                </div>
            </div>
        """)
        
        return ''.join(explanation_parts)
    
    def generate_task_help(self, message: str, account: StudentAccount) -> str:
        """生成任务帮助回复"""
        plan_data = self.get_user_study_plan(account)
        
        # 尝试从消息中提取任务和部分信息
        part_match = re.search(r'part\s*(\d+)', message.lower())
        part_number = part_match.group(1) if part_match else "2"
        
        # 如果有计划数据，尝试找到相关任务
        if plan_data and plan_data.get('aiSummary', {}).get('tasks'):
            tasks = plan_data['aiSummary']['tasks']
            if tasks:
                # 使用第一个任务作为示例
                task = tasks[0]
                task_title = task.get('taskTitle', 'Your Assignment')
                parts = task.get('parts', [])
                
                if parts and len(parts) >= int(part_number):
                    part_info = parts[int(part_number) - 1]
                    part_title = part_info.get('title', f'Part {part_number}')
                    part_notes = part_info.get('notes', 'Focus on the key requirements and break down the work into smaller steps.')
                    part_minutes = part_info.get('minutes', 60)
                    
                    return f"""
                    <div>
                        <div style="font-weight: 700; margin-bottom: 8px;">
                            Great question! Let me explain Part {part_number} of "{task_title}" for you. 🎯
                        </div>
                        <div style="line-height: 1.6;">
                            <div style="font-weight: 600; margin-bottom: 6px;">Part {part_number}: {part_title}</div>
                            <div style="margin-bottom: 12px; padding: 8px; background: #f8f9fa; border-radius: 6px;">
                                {part_notes}
                            </div>
                            <div style="font-weight: 600; margin-bottom: 6px;">Key details:</div>
                            <ul style="padding-left: 18px; margin: 0, margin-bottom: 12px;">
                                <li><strong>Estimated time:</strong> {part_minutes // 60} hour{'s' if part_minutes >= 120 else ''} ({part_minutes} minutes)</li>
                                <li><strong>Focus area:</strong> {part_title}</li>
                                <li><strong>Approach:</strong> Break into 25-30 minute focused sessions</li>
                            </ul>
                            <div style="font-weight: 600; margin-bottom: 6px;">Success tips:</div>
                            <ul style="padding-left: 18px; margin: 0;">
                                <li>Start by reviewing the specific requirements</li>
                                <li>Create a mini-checklist for this part</li>
                                <li>Take short breaks to maintain focus</li>
                                <li>Save your progress frequently</li>
                            </ul>
                        </div>
                    </div>
                    """
        
        # 默认回复
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                I'd love to help you with Part {part_number}! 📚
            </div>
            <div style="line-height: 1.6;">
                <div style="font-weight: 600; margin-bottom: 6px;">General approach for any task part:</div>
                <ul style="padding-left: 18px; margin: 0, margin-bottom: 12px;">
                    <li><strong>Read carefully:</strong> Review all requirements and rubrics</li>
                    <li><strong>Plan first:</strong> Break the part into smaller steps</li>
                    <li><strong>Time management:</strong> Use focused 25-30 minute sessions</li>
                    <li><strong>Regular breaks:</strong> Step away every hour to stay fresh</li>
                </ul>
                <div style="margin-top: 12px; font-size: 13px; color: #666;">
                    💡 For more specific guidance, generate your study plan first - then I can give you detailed, personalized advice for each part!
                </div>
            </div>
        </div>
        """
    
    def generate_encouragement(self) -> str:
        """生成鼓励回复"""
        encouragements = [
            """
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    You're doing amazing! 🌟
                </div>
                <div style="line-height: 1.6;">
                    Learning can be challenging, but every step you take is building your knowledge and skills.
                    <br /><br />
                    Remember: Progress isn't always linear. Some days will feel easier than others, and that's perfectly okay!
                    <br /><br />
                    You've already shown great dedication by seeking help and working through difficult concepts. Keep going - you've got this! 💪
                </div>
            </div>
            """,
            """
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    Take a deep breath - you're stronger than you think! 🌈
                </div>
                <div style="line-height: 1.6;">
                    It's completely normal to feel overwhelmed sometimes. What matters is that you're here, trying, and not giving up.
                    <br /><br />
                    <strong>Remember:</strong>
                    <ul style="padding-left: 18px; margin: '8px 0';">
                        <li>Every expert was once a beginner</li>
                        <li>Mistakes are proof that you're trying</li>
                        <li>Small progress is still progress</li>
                        <li>You don't have to be perfect, just persistent</li>
                    </ul>
                    Tomorrow is a fresh start. You've got this! ✨
                </div>
            </div>
            """
        ]
        
        import random
        return random.choice(encouragements)
    
    def generate_practice_response(self) -> str:
        """生成练习建议回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                I understand this topic feels challenging! That's completely normal. 🎯
            </div>
            <div style="margin-bottom: 10px;">
                Based on your progress, I've created a focused 10-minute practice session targeting the areas you're finding difficult.
            </div>
            <button
                class="cw-cta-btn"
                onclick="window.startPracticeSession && window.startPracticeSession()"
                aria-label="Start practice"
            >
                Start 10-minute practice session
                <span style="margin-left: 8px;">→</span>
            </button>
            <div style="margin-top: 12px; font-size: 13px; color: #666;">
                This practice will help reinforce key concepts and build your confidence!
            </div>
        </div>
        """
    
    def generate_greeting_response(self) -> str:
        """生成问候回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Hello! 👋 I'm your AI Learning Coach.
            </div>
            <div style="line-height: 1.6;">
                I'm here to help you with your study plan, answer questions about your assignments, 
                provide practice exercises, and offer encouragement when you need it!
                <br /><br />
                How can I assist you with your learning today?
            </div>
        </div>
        """
    
    def generate_general_response(self) -> str:
        """生成通用回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                I'd love to help you with that! 🤔
            </div>
            <div style="line-height: 1.6;">
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
    
    def generate_ai_response(self, message: str, account: StudentAccount, conversation_history: Optional[list[dict[str, Any]]] = None) -> str:
        """使用Gemini AI生成智能回复"""
        if not use_gemini:
            # 如果没有AI，回退到基于规则的回复
            intent = self.detect_intent(message)
            if intent == 'explain_plan':
                return self.generate_plan_explanation(account)
            elif intent == 'task_help':
                return self.generate_task_help(message, account)
            elif intent == 'encouragement':
                return self.generate_encouragement()
            elif intent == 'practice':
                return self.generate_practice_response()
            elif intent == 'greeting':
                return self.generate_greeting_response()
            else:
                return self.generate_general_response()
        
        try:
            # 获取用户的学习计划信息
            plan_data = self.get_user_study_plan(account)
            plan_context = ""
            if plan_data:
                ai_summary = plan_data.get('aiSummary', {})
                tasks = ai_summary.get('tasks', [])
                if tasks:
                    plan_context = f"\n\nUser's current study plan includes {len(tasks)} tasks: "
                    for task in tasks[:3]:  # 只包含前3个任务
                        task_title = task.get('taskTitle', 'Unknown Task')
                        parts_count = len(task.get('parts', []))
                        plan_context += f"\n- {task_title} ({parts_count} parts)"
            
            # 构建对话历史上下文
            history_context = ""
            if conversation_history:
                recent_messages = conversation_history[-6:]  # 最近6条消息
                history_context = "\n\nRecent conversation:\n"
                for msg in recent_messages:
                    role = "Student" if msg['type'] == 'user' else "Coach"
                    content = msg['content'][:200]  # 限制长度
                    history_context += f"{role}: {content}\n"
            
            # 构建AI提示
            system_prompt = f"""You are an AI Learning Coach helping university students with their studies. You are supportive, encouraging, and provide practical advice.

Your role:
- Help students understand their study plans and assignments
- Provide guidance on specific tasks and parts
- Offer encouragement when students feel overwhelmed
- Suggest practice exercises for difficult topics
- Answer questions about academic work

Guidelines:
- Be warm, supportive, and encouraging
- Provide specific, actionable advice
- Keep responses concise but helpful (max 200 words)
- Use a friendly, conversational tone
- Include relevant emojis to make responses more engaging
- Respond in plain text format, no HTML or markdown
- Address the student naturally without always using their name, or use their actual name if needed: {account.name or 'there'}

Student context:
- Student ID: {account.student_id}
- Name: {account.name or 'Student'}{plan_context}{history_context}

Current student message: {message}

Respond as their AI Learning Coach. Do not use "Test Student" - address them naturally or by their actual name."""

            # 调用Gemini AI
            response = _model.generate_content(system_prompt)
            
            if response and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    ai_text = ""
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            ai_text += part.text
                    
                    if ai_text.strip():
                        # 清理AI回复中的HTML标签和markdown格式
                        cleaned_text = self.clean_ai_response(ai_text)
                        return cleaned_text
            
            # 如果AI回复失败，回退到基于规则的回复
            return self.generate_general_response()
            
        except Exception as e:
            print(f"[DEBUG] AI回复生成失败: {e}")
            # 回退到基于规则的回复
            return self.generate_general_response()
    
    def process_message(self, account: StudentAccount, message: str) -> dict[str, Any]:
        """处理用户消息并生成AI回复"""
        try:
            # 获取或创建对话会话
            conversation = self.get_or_create_conversation(account)
            
            # 获取对话历史用于上下文
            conversation_history = self.get_conversation_history(account, limit=10)
            
            # 检查是否是欢迎消息（自动发送的初始化消息）
            if message.lower().strip() == 'welcome':
                # 对于欢迎消息，不保存用户消息，只返回AI的欢迎回复
                ai_response = self.generate_welcome_response()
                
                # 保存AI回复
                ai_message = ChatMessage.objects.create(  # type: ignore
                    conversation=conversation,
                    message_type='ai',
                    content=ai_response,
                    metadata={'intent': 'welcome', 'ai_powered': False, 'is_welcome': True}
                )
                
                return {
                    'success': True,
                    'ai_response': {
                        'id': ai_message.id,  # type: ignore
                        'content': ai_message.content,  # type: ignore
                        'timestamp': ai_message.timestamp.isoformat(),  # type: ignore
                        'type': 'ai',
                        'intent': 'welcome',
                        'ai_powered': False
                    }
                }
            
            # 对于用户的真实消息，正常处理
            # 保存用户消息
            print(f"[DEBUG] 保存用户消息到数据库: user={account.student_id}, message={message}")
            user_message = ChatMessage.objects.create(  # type: ignore
                conversation=conversation,
                message_type='user',
                content=message
            )
            print(f"[DEBUG] 用户消息已保存，ID: {user_message.id}")
            
            # 更新对话的最后活动时间
            from django.utils import timezone
            conversation.last_activity_at = timezone.now()
            conversation.save()
            
            # 检测意图
            intent = self.detect_intent(message)
            
            # 根据意图生成回复
            if intent == 'explain_plan':
                # 对于计划解释请求，返回保存的计划描述
                ai_response = self.generate_plan_explanation(account)
            else:
                # 对于其他消息，使用AI生成智能回复
                ai_response = self.generate_ai_response(message, account, conversation_history)
            
            # 保存AI回复
            print(f"[DEBUG] 保存AI回复到数据库: user={account.student_id}, response={ai_response[:50]}...")
            ai_message = ChatMessage.objects.create(  # type: ignore
                conversation=conversation,
                message_type='ai',
                content=ai_response,
                metadata={'intent': intent, 'ai_powered': use_gemini and intent != 'explain_plan'}
            )
            print(f"[DEBUG] AI回复已保存，ID: {ai_message.id}")
            
            return {
                'success': True,
                'user_message': {
                    'id': user_message.id,  # type: ignore
                    'content': user_message.content,  # type: ignore
                    'timestamp': user_message.timestamp.isoformat(),  # type: ignore
                    'type': 'user'
                },
                'ai_response': {
                    'id': ai_message.id,  # type: ignore
                    'content': ai_message.content,  # type: ignore
                    'timestamp': ai_message.timestamp.isoformat(),  # type: ignore
                    'type': 'ai',
                    'intent': intent,
                    'ai_powered': use_gemini and intent != 'explain_plan'
                }
            }
            
        except Exception as e:
            print(f"[DEBUG] 消息处理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversation_history(self, account: StudentAccount, limit: int = 50) -> list[dict[str, Any]]:
        """获取用户的对话历史"""
        try:
            print(f"[DEBUG] 获取对话历史: user={account.student_id}, limit={limit}")
            # 创建临时User对象用于查询
            user, _ = User.objects.get_or_create(  # type: ignore
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            conversation = ChatConversation.objects.filter(user=user, is_active=True).first()  # type: ignore
            if not conversation:
                print(f"[DEBUG] 没有找到对话记录: user={account.student_id}")
                return []
            
            # 获取最新的消息，按时间戳倒序排列，然后取前limit条
            messages = conversation.messages.order_by('-timestamp')[:limit]  # type: ignore
            print(f"[DEBUG] 找到 {len(messages)} 条消息: user={account.student_id}")
            
            return [
                {
                    'id': msg.id,  # type: ignore
                    'type': msg.message_type,  # type: ignore
                    'content': msg.content,  # type: ignore
                    'timestamp': msg.timestamp.isoformat(),  # type: ignore
                    'metadata': msg.metadata  # type: ignore
                }
                for msg in messages
            ]
            
        except Exception:
            return []
    
    def save_study_plan(self, account: StudentAccount, plan_data: dict[str, Any]) -> bool:
        """保存用户的学习计划数据"""
        try:
            # 创建临时User对象
            user, _ = User.objects.get_or_create(  # type: ignore
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            
            # 将之前的计划设为非活跃
            UserStudyPlan.objects.filter(user=user, is_active=True).update(is_active=False)  # type: ignore
            
            # 创建新的活跃计划
            UserStudyPlan.objects.create(  # type: ignore
                user=user,
                plan_data=plan_data,
                is_active=True
            )
            
            return True
        except Exception:
            return False
    
    def clean_ai_response(self, text: str) -> str:
        """清理AI回复中的HTML标签和markdown格式"""
        import re
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除markdown代码块
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        
        # 移除多余的空白行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # 清理开头和结尾的空白
        text = text.strip()
        
        return text
    
    def generate_welcome_response(self) -> str:
        """生成固定的欢迎回复"""
        return """Hello! 👋 I'm your AI Learning Coach.

I'd love to help you with that! 🤔

To give you the best assistance, could you tell me a bit more about what you're working on?

You can ask me about:

• Your study plan and schedule

• Practice exercises for difficult topics

• Or just ask for some encouragement!"""