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
            'practice': [
                r'practice', r'weak.*topic', r'difficult.*topic',
                r'need.*help.*with', r'don.*understand', r'struggling.*with',
                r'weak.*in', r'find.*difficult', r'bad.*at'
            ],
            'encouragement': [
                r'encourage', r'motivation', r'feel.*bad', r'hard.*time',
                r'anxious', r'worried', r'overwhelm', r'stress'
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
    
    def is_practice_request(self, message: str) -> bool:
        """检测是否是练习请求"""
        practice_keywords = [
            'practice', 'weak topic', 'difficult topic', 'need help with', 
            'don\'t understand', 'struggling with', 'weak in', 'find difficult',
            'bad at', 'want to practice', 'need practice', 'practice session'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in practice_keywords)
    
    def is_in_practice_flow(self, conversation_history: list[dict[str, Any]]) -> bool:
        """检查是否处于练习流程中"""
        if not conversation_history:
            return False
        
        # 查找最近的AI消息
        last_ai_message = None
        for msg in conversation_history:
            if msg['type'] == 'ai':
                last_ai_message = msg
                break
        
        if not last_ai_message:
            return False
        
        content = last_ai_message['content']
        
        # 检查是否包含练习流程的标识文本
        practice_flow_indicators = [
            'which course would you like to practise?',
            'which topic would you like to focus on?',
            'which topic would you like to work on?',
            'here are some topics available for this course:',
            'here are the courses you\'re currently enrolled in:',
            'which course is this topic for?',
            'i\'m not seeing that course in your enrolments',
            'i\'m not able to match that to a topic in this course'
        ]
        
        return any(indicator in content.lower() for indicator in practice_flow_indicators)
    
    def get_student_courses(self, account: StudentAccount) -> list[str]:
        """获取学生注册的课程列表"""
        try:
            from courses.models import StudentEnrollment
            enrollments = StudentEnrollment.objects.filter(student_id=account.student_id)
            return [enrollment.course_code for enrollment in enrollments]
        except Exception as e:
            print(f"[DEBUG] 获取学生课程失败: {e}")
            return []
    
    def get_course_topics(self, course_code: str) -> list[str]:
        """获取课程的题目主题列表"""
        try:
            from courses.models import QuestionKeyword, QuestionKeywordMap
            topics = QuestionKeyword.objects.filter(
                questionkeywordmap__question__course_code=course_code
            ).values_list('name', flat=True).distinct()
            return list(topics)
        except Exception as e:
            print(f"[DEBUG] 获取课程主题失败: {e}")
            return []
    
    def validate_course_input(self, user_input: str, available_courses: list[str]) -> tuple[bool, str]:
        """验证用户输入的课程是否有效"""
        user_input_clean = user_input.strip().upper()
        
        # 精确匹配
        if user_input_clean in available_courses:
            return True, user_input_clean
        
        # 模糊匹配（去除空格后比较）
        user_input_no_space = user_input_clean.replace(' ', '')
        for course in available_courses:
            if course.replace(' ', '') == user_input_no_space:
                return True, course
        
        # 部分匹配（如果输入了课程代码的一部分）
        for course in available_courses:
            if user_input_clean in course or course in user_input_clean:
                return True, course
        
        return False, None
    
    # ==================== 练习状态管理方法 ====================
    
    def set_practice_setup_mode(self, user_id: str, step: str, course: str = None, topic: str = None):
        """设置练习设置模式"""
        from .models import PracticeSetupState
        
        state, created = PracticeSetupState.objects.update_or_create(
            student_id=user_id,
            defaults={
                'step': step,
                'course': course,
                'topic': topic
            }
        )
        
        if not created:
            state.step = step
            state.course = course
            state.topic = topic
            state.save()
        
        print(f"[DEBUG] 设置练习模式: user={user_id}, step={step}, course={course}, topic={topic}")
    
    def get_practice_setup_state(self, user_id: str) -> Optional[dict[str, Any]]:
        """获取练习设置状态"""
        from .models import PracticeSetupState
        
        try:
            state = PracticeSetupState.objects.get(student_id=user_id)
            return {
                'step': state.step,
                'course': state.course,
                'topic': state.topic
            }
        except PracticeSetupState.DoesNotExist:
            return None
    
    def clear_practice_setup_mode(self, user_id: str):
        """清除练习设置模式"""
        from .models import PracticeSetupState
        
        try:
            state = PracticeSetupState.objects.get(student_id=user_id)
            state.delete()
            print(f"[DEBUG] 清除练习模式: user={user_id}")
        except PracticeSetupState.DoesNotExist:
            pass
    
    def is_in_practice_setup_mode(self, user_id: str) -> bool:
        """检查是否在练习设置模式中"""
        from .models import PracticeSetupState
        
        return PracticeSetupState.objects.filter(student_id=user_id).exists()
    
    def handle_practice_setup_mode(self, account: StudentAccount, message: str) -> Optional[str]:
        """处理练习设置模式下的用户输入"""
        user_id = account.student_id
        print(f"[DEBUG] handle_practice_setup_mode 被调用: user={user_id}, message={message}")
        state = self.get_practice_setup_state(user_id)
        
        if not state:
            return None
        
        step = state['step']
        print(f"[DEBUG] 当前步骤: {step}")
        available_courses = self.get_student_courses(account)
        
        if step == 'course':
            # 处理课程选择
            is_valid, validated_course = self.validate_course_input(message, available_courses)
            
            if is_valid:
                # 课程有效，进入主题选择步骤
                topics = self.get_course_topics(validated_course)
                if topics:
                    self.set_practice_setup_mode(user_id, 'topic', validated_course)
                    return f"""
                    <div>
                        <div style="font-weight: 700; margin-bottom: 8px;">
                            Awesome, we'll practise {validated_course} 🙌
                        </div>
                        <div style="margin-bottom: 12px;">
                            Here are some topics covered in this course:
                        </div>
                        <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                            {chr(10).join(f'• {topic}' for topic in topics)}
                        </div>
                        <div>
                            Please type the topic name you want to practise.
                        </div>
                    </div>
                    """
                else:
                    # 没有找到主题，清除模式并返回错误
                    self.clear_practice_setup_mode(user_id)
                    return f"""
                    <div>
                        <div style="font-weight: 700; margin-bottom: 8px;">
                            No topics found for {validated_course} 😅
                        </div>
                        <div style="margin-bottom: 12px;">
                            It looks like there are no practice questions available for this course yet.
                        </div>
                        <div>
                            Please try another course or contact your instructor.
                        </div>
                    </div>
                    """
            else:
                # 课程无效，显示错误并重新提示
                return f"""
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        I couldn't detect this course 🤔
                    </div>
                    <div style="margin-bottom: 12px;">
                        Please check the spelling and choose from your enrolled courses:
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                        {', '.join(available_courses)}
                    </div>
                    <div>
                        Please type the course name you want to practise.
                    </div>
                </div>
                """
        
        elif step == 'topic':
            # 处理主题选择
            course = state['course']
            topics = self.get_course_topics(course)
            print(f"[DEBUG] 主题验证: course={course}, available_topics={topics}, user_input={message}")
            is_valid, validated_topic = self.validate_topic_input(message, topics)
            print(f"[DEBUG] 主题验证结果: is_valid={is_valid}, validated_topic={validated_topic}")
            
            if is_valid:
                # 主题有效，生成练习
                self.clear_practice_setup_mode(user_id)  # 清除设置模式
                return self.generate_practice_for_topic(course, validated_topic)
            else:
                # 主题无效，显示错误并重新提示
                return f"""
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        I'm not able to match that to a topic in this course 😅
                    </div>
                    <div style="margin-bottom: 12px;">
                        Please check the spelling and try again by choosing a topic from the list above.
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                        {chr(10).join(f'• {topic}' for topic in topics)}
                    </div>
                    <div>
                        Please type the topic name you want to practise.
                    </div>
                </div>
                """
        
        elif step == 'generating':
            # 已经在生成阶段，清除模式
            self.clear_practice_setup_mode(user_id)
            return None
        
        return None
    

    

    

    
    def extract_course_and_topic_from_message(self, message: str, available_courses: list[str]) -> tuple[str, str]:
        """从消息中提取课程和主题信息"""
        # 提取课程
        course = None
        for course_code in available_courses:
            if course_code.lower() in message.lower():
                course = course_code
                break
        
        # 提取主题（使用现有的薄弱项提取逻辑）
        topic = self.extract_weak_topic(message)
        
        return course, topic
    
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
            return """<div><div style="font-weight: 700; margin-bottom: 8px;">I don't see an active study plan for you yet. 📋</div><div style="line-height: 1.6;">To get a personalized explanation, please generate your study plan first from the "My Plan" section.<br /><br />Once you have a plan, I can explain:<ul style="padding-left: 18px; margin: 8px 0;"><li>Why tasks are scheduled in a specific order</li><li>How deadlines and workload are balanced</li><li>Tips for following your personalized schedule</li></ul></div></div>"""
        
        # 提取计划信息
        ai_summary = plan_data.get('aiSummary', {})
        tasks = ai_summary.get('tasks', [])
        
        # 构建解释内容 - 使用更紧凑的格式
        explanation_parts = []
        
        # 总体说明
        explanation_parts.append("""<div><div style="font-weight: 700; margin-bottom: 8px;">Hi! Here's a detailed explanation of your personalized learning plan. ✨</div>""")
        
        # 计划创建逻辑
        explanation_parts.append("""<div style="font-weight: 600; margin-bottom: 4px;">How your plan was created:</div><ul style="padding-left: 18px; margin: 0;"><li><strong>Course analysis:</strong> AI analyzed all your course requirements and deadlines</li><li><strong>Task breakdown:</strong> Each assignment was intelligently split into manageable parts</li><li><strong>Time allocation:</strong> Hours distributed based on task complexity and your preferences</li><li><strong>Schedule optimization:</strong> Tasks arranged to avoid conflicts and maintain steady progress</li></ul>""")
        
        # 任务详情
        if tasks:
            explanation_parts.append(f"""<div style="font-weight: 600; margin: 8px 0 4px;">Your plan includes {len(tasks)} main tasks:</div><ul style="padding-left: 18px; margin: 0;">""")
            
            for task in tasks[:3]:  # 只显示前3个任务避免过长
                task_title = task.get('taskTitle', 'Unknown Task')
                parts_count = len(task.get('parts', []))
                total_minutes = task.get('totalMinutes', 0)
                hours = total_minutes // 60
                
                explanation_parts.append(f"""<li><strong>{task_title}:</strong> {parts_count} parts, ~{hours} hours total</li>""")
            
            if len(tasks) > 3:
                explanation_parts.append(f"<li><em>...and {len(tasks) - 3} more tasks</em></li>")
            
            explanation_parts.append("</ul>")
        
        # 使用提示
        explanation_parts.append("""<div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 6px;"><div style="font-weight: 600; margin-bottom: 4px;">💡 Pro Tips:</div><div>• Your plan automatically adapts if you miss a day<br/>• Each task is broken into focused work sessions<br/>• Ask me about specific parts for detailed guidance!</div></div></div>""")
        
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
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
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
    
    def extract_weak_topic(self, message: str) -> str:
        """从消息中提取薄弱项主题"""
        import re
        
        # 尝试多种模式匹配具体主题
        topic_patterns = [
            r'(?:weak.*in|struggling.*with|difficulty.*with|薄弱.*在|困难.*在|不擅长|不太会|搞不懂)\s*([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            r'(?:topic|主题|方面|领域)\s*[:：]?\s*([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            r'(?:help.*with|help.*me.*with|需要.*帮助|帮我.*?)([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            r'(?:find.*difficult|find.*challenging|find.*hard)\s+([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            # 新增模式：直接匹配topic名称（用于对话式选择）
            r'(?:want.*practice|need.*help|practice|help)\s+(?:with\s+)?([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            # 匹配单独的topic名称
            r'^([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))$'
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).strip()
        
        return None
    
    def extract_topic_from_response(self, message: str, available_topics: list[str]) -> str:
        """从用户回复中提取topic名称"""
        import re
        
        message_lower = message.lower().strip()
        
        # 首先尝试精确匹配
        for topic in available_topics:
            if topic.lower() in message_lower:
                return topic
        
        # 尝试模糊匹配
        for topic in available_topics:
            topic_words = topic.lower().split()
            for word in topic_words:
                if len(word) > 3 and word in message_lower:  # 匹配长度大于3的单词
                    return topic
        
        return None
    
    def extract_course_from_message(self, message: str) -> str:
        """从消息中提取课程代码"""
        import re
        
        # 课程代码模式 - 扩展模式以匹配更多表达方式
        course_patterns = [
            r'(?:course|课程)\s*([A-Z]{4}\d{4})',
            r'([A-Z]{4}\d{4})\s*(?:course|课程)?',
            r'(?:in|for|about)\s+([A-Z]{4}\d{4})',
            r'(?:help.*with|practice|study|learn|need.*help)\s+([A-Z]{4}\d{4})',
            r'([A-Z]{4}\d{4})(?:\s+|$)',  # 匹配独立的课程代码
        ]
        
        for pattern in course_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).upper()
        
        return None
    
    def generate_course_topic_selection(self, course_code: str) -> str:
        """生成课程topic选择界面 - 对话形式，支持任何课程"""
        try:
            from courses.models import Question, QuestionKeyword
            from django.db.models import Count
            
            # 获取该课程的所有关键词和题目数量
            course_keywords = QuestionKeyword.objects.filter(
                questionkeywordmap__question__course_code=course_code
            ).annotate(
                question_count=Count('questionkeywordmap__question')
            ).order_by('-question_count')
            
            if not course_keywords.exists():
                return f"""
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        I don't see any specific topics for {course_code} yet. 📚
                    </div>
                    <div style="margin-bottom: 10px;">
                        Let me help you with general practice for this course.
                    </div>
                    <button
                        class="cw-cta-btn"
                        onclick="window.startPracticeSession && window.startPracticeSession('{course_code}')"
                        aria-label="Start general practice for {course_code}"
                    >
                        Start {course_code} General Practice
                        <span style="margin-left: 8px;">→</span>
                    </button>
                </div>
                """
            
            # 构建topic列表 - 对话形式
            topic_list = ""
            for i, keyword in enumerate(course_keywords, 1):
                topic_name = keyword.name
                question_count = keyword.question_count
                topic_list += f"{i}. {topic_name.title()} ({question_count} questions)\n"
            
            # 获取第一个topic作为示例
            first_topic = course_keywords.first().name if course_keywords.first() else "algorithms"
            
            return f"""
            <div>
                <div style="margin-bottom: 12px;">
                    Available topics for {course_code}:
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace; white-space: pre-line;">
{topic_list}
                </div>
                <div style="margin-bottom: 10px;">
                    Which topic would you like to practice?
                </div>
            </div>
            """
            
        except Exception as e:
            print(f"[DEBUG] Error generating course topic selection: {e}")
            return self.generate_practice_response()
    
    def is_topic_specific(self, topic: str) -> bool:
        """检查主题是否足够具体"""
        if not topic or len(topic) < 3:
            return False
        
        # 检查是否包含技术关键词
        technical_keywords = [
            'data', 'algorithm', 'program', 'python', 'java', 'javascript', 'loop', 'function', 
            'variable', 'array', 'list', 'dictionary', 'recursion', 'sort', 'search', 'class', 
            'object', 'inheritance', 'database', 'sql', 'web', 'html', 'css', 'react', 'vue', 
            'angular', 'node', 'express', 'django', 'flask', 'machine', 'learning', 'ai', 
            'neural', 'network', 'deep', 'statistic', 'probability', 'math', 'calculus', 
            'computer', 'software', 'complexity', 'dynamic', 'greedy', 'divide', 'conquer', 
            'backtrack', 'graph', 'tree', 'linked', 'stack', 'queue', 'hash', 'binary', 
            'heap', 'priority', 'bubble', 'quick', 'merge', 'insertion', 'selection', 
            'counting', 'radix', 'bucket', 'mining', 'classification', 'clustering', 'unsupervised',
            'supervised', 'regression', 'decision', 'tree', 'kmeans', 'pca', 'apriori'
        ]
        
        has_technical_keyword = any(keyword in topic.lower() for keyword in technical_keywords)
        
        # 排除过于模糊的表述
        vague_terms = ['everything', 'anything', 'something', 'stuff', 'things', 'all', 'general']
        is_vague = any(term in topic.lower() for term in vague_terms)
        
        return has_technical_keyword and not is_vague
    
    def generate_practice_response(self, topic: str = None) -> str:
        """生成练习建议回复"""
        if topic:
            topic_display = topic.title()
            return f"""
            <div>
                <div style="margin-bottom: 12px;">
                    Got it! Let's practice <strong>{topic_display}</strong> together.
                </div>
                <button
                    class="cw-cta-btn"
                    onclick="window.startPracticeSession && window.startPracticeSession('{topic}')"
                    aria-label="Start practice for {topic}"
                >
                    Start Practice
                    <span style="margin-left: 8px;">→</span>
                </button>
            </div>
            """
        else:
            return """
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    Got it! Let's start a practice session to help you improve.
                </div>
                <button
                    class="cw-cta-btn"
                    onclick="window.startPracticeSession && window.startPracticeSession()"
                    aria-label="Start practice"
                >
                    Start Practice
                    <span style="margin-left: 8px;">→</span>
                </button>
            </div>
            """
    
    def generate_clarification_response(self) -> str:
        """生成澄清请求回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                I'd love to help you with targeted practice! 🤔
            </div>
            <div style="margin-bottom: 12px;">
                To provide you with the most relevant practice questions, could you please be more specific about which topic or concept you're finding difficult?
            </div>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="font-weight: 600; margin-bottom: 8px; color: #495057;">For example, you could say:</div>
                <div style="font-size: 14px; line-height: 1.5; color: #6c757d;">
                    • "I'm struggling with <strong>data structures like arrays and linked lists</strong>"<br>
                    • "I need practice with <strong>Python loops and functions</strong>"<br>
                    • "I find it difficult to understand <strong>algorithms</strong>"<br>
                    • "I'm weak in <strong>database queries and SQL</strong>"<br>
                    • "I don't understand <strong>recursion and dynamic programming</strong>"
                </div>
            </div>
            <div style="font-size: 14px; color: #6c757d; font-style: italic;">
                Once you tell me the specific topic, I'll generate personalized practice questions just for you! 💪
            </div>
        </div>
        """
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
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
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
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
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
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
                # 检查是否提到了具体课程
                course_code = self.extract_course_from_message(message)
                if course_code:
                    return self.generate_course_topic_selection(course_code)
                else:
                    # 检查是否有明确的薄弱项主题
                    topic = self.extract_weak_topic(message)
                    if topic and self.is_topic_specific(topic):
                        return self.generate_practice_response(topic)
                    else:
                        return self.generate_clarification_response()
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
            
            # 优先检查是否在练习设置模式中
            if self.is_in_practice_setup_mode(account.student_id):
                # 在练习设置模式中，使用专门的处理逻辑
                ai_response = self.handle_practice_setup_mode(account, message)
                if ai_response is None:
                    # 如果返回None，说明模式已结束，回退到普通处理
                    self.clear_practice_setup_mode(account.student_id)
                    intent = self.detect_intent(message)
                    ai_response = self.generate_general_response()
                else:
                    # 在练习设置模式中，设置intent为practice
                    intent = 'practice'
            else:
                # 检测意图
                intent = self.detect_intent(message)
                
                # 检查是否是练习请求,如果是,启动练习设置模式
                if self.is_practice_request(message):
                    # 先检查用户是否已经提供了课程和主题
                    available_courses = self.get_student_courses(account)
                    mentioned_course, mentioned_topic = self.extract_course_and_topic_from_message(message, available_courses)
                    
                    print(f"[DEBUG] 练习请求检测: 课程={mentioned_course}, 主题={mentioned_topic}")
                    
                    # 如果用户同时提供了课程和主题,直接生成练习
                    if mentioned_course and mentioned_topic:
                        # 验证课程和主题
                        is_course_valid, valid_course = self.validate_course_input(mentioned_course, available_courses)
                        if is_course_valid:
                            topics = self.get_course_topics(valid_course)
                            is_topic_valid, valid_topic = self.validate_topic_input(mentioned_topic, topics)
                            
                            if is_topic_valid:
                                # 课程和主题都有效,返回"正在生成"消息，让前端处理
                                print(f"[DEBUG] 开始练习生成流程: {valid_course} - {valid_topic}")
                                ai_response = f"""
                                <div>
                                    <div style="font-weight: 700; margin-bottom: 8px;">
                                        Great choice 💪
                                    </div>
                                    <div style="margin-bottom: 12px;">
                                        I'm now generating a practice set for {valid_course} – {valid_topic}.
                                        Please wait a moment…
                                    </div>
                                </div>
                                """
                            else:
                                # 主题无效
                                self.set_practice_setup_mode(account.student_id, 'topic', valid_course)
                                ai_response = f"""
                        <div>
                            <div style="font-weight: 700; margin-bottom: 8px;">
                                I couldn't find that topic in {valid_course} 😅
                            </div>
                            <div style="margin-bottom: 12px;">
                                Here are some topics covered in this course:
                            </div>
                            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                                {chr(10).join(f'• {topic}' for topic in topics)}
                            </div>
                            <div>
                                Please type the topic name you want to practise.
                            </div>
                        </div>
                        """
                        else:
                            # 课程无效
                            self.set_practice_setup_mode(account.student_id, 'course')
                            ai_response = f"""
                        <div>
                            <div style="font-weight: 700; margin-bottom: 8px;">
                                I couldn't find that course 😅
                            </div>
                            <div style="margin-bottom: 12px;">
                                Here are the courses you're currently enrolled in:
                            </div>
                            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                                {', '.join(available_courses)}
                            </div>
                            <div>
                                Please type the course name you want to practise.
                            </div>
                        </div>
                        """
                    # 如果没有提供课程和主题,启动练习设置模式
                    else:
                        if available_courses:
                            self.set_practice_setup_mode(account.student_id, 'course')
                            ai_response = f"""
                        <div>
                            <div style="font-weight: 700; margin-bottom: 8px;">
                                Great idea to work on your weak topics 😊
                            </div>
                            <div style="margin-bottom: 12px;">
                                Before we start, which course would you like to practise?
                            </div>
                            <div style="margin-bottom: 12px;">
                                Here are the courses you're currently enrolled in:
                            </div>
                            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                                {', '.join(available_courses)}
                            </div>
                            <div>
                                Please type the course name you want to practise.
                            </div>
                        </div>
                        """
                        else:
                            ai_response = """
                        <div>
                            <div style="font-weight: 700; margin-bottom: 8px;">
                                I don't see any courses in your enrollment yet 📚
                            </div>
                            <div style="line-height: 1.6;">
                                To get started with practice, please enroll in some courses first. 
                                You can do this from the "My Courses" section.
                            </div>
                        </div>
                        """
                else:
                    # 普通模式：根据意图生成回复
                    if intent == 'explain_plan':
                        # 对于计划解释请求，返回保存的计划描述
                        ai_response = self.generate_plan_explanation(account)
                    elif intent == 'task_help':
                        # 对于任务帮助请求，生成任务相关的回复
                        ai_response = self.generate_ai_response(message, account, conversation_history)
                    elif intent == 'encouragement':
                        # 对于鼓励请求，生成鼓励性回复
                        ai_response = self.generate_ai_response(message, account, conversation_history)
                    elif intent == 'greeting':
                        # 对于问候，生成问候回复
                        ai_response = self.generate_ai_response(message, account, conversation_history)
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
    
    def get_conversation_history(self, account: StudentAccount, limit: int = 50, days: int = None) -> list[dict[str, Any]]:
        """获取用户的对话历史
        
        Args:
            account: 学生账户
            limit: 限制返回的消息数量
            days: 限制返回的天数范围，如果为None则返回所有消息
        """
        try:
            print(f"[DEBUG] 获取对话历史: user={account.student_id}, limit={limit}, days={days}")
            # 创建临时User对象用于查询
            user, _ = User.objects.get_or_create(  # type: ignore
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            conversation = ChatConversation.objects.filter(user=user, is_active=True).first()  # type: ignore
            if not conversation:
                print(f"[DEBUG] 没有找到对话记录: user={account.student_id}")
                return []
            
            # 构建查询条件
            messages_query = conversation.messages.all()  # type: ignore
            
            # 如果指定了天数限制，添加时间过滤
            if days is not None:
                from django.utils import timezone
                from datetime import timedelta
                cutoff_date = timezone.now() - timedelta(days=days)
                messages_query = messages_query.filter(timestamp__gte=cutoff_date)
                print(f"[DEBUG] 时间过滤: 只显示 {days} 天内的消息 (从 {cutoff_date} 开始)")
            
            # 获取最新的消息，按时间戳倒序排列，然后取前limit条
            messages = messages_query.order_by('-timestamp')[:limit]  # type: ignore
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
    
    def handle_practice_flow(self, account: StudentAccount, message: str, conversation_history: list[dict[str, Any]]) -> str:
        """处理多步骤练习对话流程"""
        # 获取学生的课程列表
        available_courses = self.get_student_courses(account)
        
        if not available_courses:
            return """
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    I don't see any courses in your enrollment yet. 📚
                </div>
                <div style="line-height: 1.6;">
                    To get started with practice, please enroll in some courses first. 
                    You can do this from the "My Courses" section.
                </div>
            </div>
            """
        
        # 检查对话历史，确定当前处于哪个步骤
        current_step = self.detect_practice_step(conversation_history)
        
        # 从消息中提取课程和主题
        mentioned_course, mentioned_topic = self.extract_course_and_topic_from_message(message, available_courses)
        
        print(f"[DEBUG] 练习流程: 当前步骤={current_step}, 提及课程={mentioned_course}, 提及主题={mentioned_topic}")
        
        # 如果处于等待课程选择的步骤
        if current_step == 'waiting_for_course':
            # 验证用户输入的课程
            is_valid, valid_course = self.validate_course_input(message, available_courses)
            if not is_valid:
                courses_text = ', '.join(available_courses)
                return f"""
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        Hmm, I couldn't find that course in your list 🤔
                    </div>
                    <div style="margin-bottom: 12px;">
                        Please check the spelling and try again by choosing a course from here:
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                        {courses_text}
                    </div>
                    <div>
                        Please type the course name you want to practise.
                    </div>
                </div>
                """
            else:
                # 课程有效，进入主题选择
                return self.handle_case_2_step_1(valid_course, available_courses, account)
        
        # 如果处于等待主题选择的步骤
        elif current_step == 'waiting_for_topic' or current_step == 'waiting_for_topic_selection':
            # 需要先确定当前讨论的是哪个课程
            current_course = self.extract_current_course_from_history(conversation_history)
            if not current_course:
                return self.handle_case_1_step_1(available_courses)
            
            # 验证用户输入的主题
            available_topics = self.get_course_topics(current_course)
            is_valid, valid_topic = self.validate_topic_input(message, available_topics)
            
            if not is_valid:
                topics_text = '\n'.join([f"• {t.title()}" for t in available_topics[:10]])
                return f"""
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        I'm not able to match that to a topic in this course 😅
                    </div>
                    <div style="margin-bottom: 12px;">
                        Please check the spelling and try again by choosing a topic from the list above.
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                        {topics_text}
                    </div>
                    <div>
                        Please type the topic name you want to practise.
                    </div>
                </div>
                """
            else:
                # 主题有效，生成练习
                return self.generate_practice_for_topic(current_course, valid_topic)
        
        # Case 1: 用户没有指定课程或主题（新对话）
        if not mentioned_course and not mentioned_topic:
            return self.handle_case_1_step_1(available_courses)
        
        # Case 2: 用户指定了课程但没有主题
        elif mentioned_course and not mentioned_topic:
            return self.handle_case_2_step_1(mentioned_course, available_courses, account)
        
        # Case 3: 用户指定了主题但没有课程
        elif not mentioned_course and mentioned_topic:
            return self.handle_case_3_step_1(mentioned_topic, available_courses)
        
        # Case 4: 用户同时指定了课程和主题
        else:
            return self.handle_complete_selection(mentioned_course, mentioned_topic, account)
    
    def extract_current_course_from_history(self, conversation_history: list[dict[str, Any]]) -> str:
        """从对话历史中提取当前讨论的课程"""
        if not conversation_history:
            return None
        
        # 查找最近的AI消息
        for msg in conversation_history:
            if msg['type'] == 'ai':
                content = msg['content']
                
                # 尝试从消息中提取课程代码
                import re
                course_match = re.search(r'practise? ([A-Z]{4}\d{4})', content, re.IGNORECASE)
                if course_match:
                    return course_match.group(1).upper()
                
                course_match = re.search(r'available topics for ([A-Z]{4}\d{4})', content, re.IGNORECASE)
                if course_match:
                    return course_match.group(1).upper()
        
        return None
    
    def detect_practice_step(self, conversation_history: list[dict[str, Any]]) -> str:
        """检测当前练习对话处于哪个步骤"""
        if not conversation_history:
            return 'start'
        
        # 查找最近的AI消息
        last_ai_message = None
        for msg in conversation_history:
            if msg['type'] == 'ai':
                last_ai_message = msg
                break
        
        if not last_ai_message:
            return 'start'
        
        content = last_ai_message['content']
        
        # 检查各种步骤的标识文本
        if 'which course would you like to practise?' in content.lower():
            return 'waiting_for_course'
        elif 'which topic would you like to focus on?' in content.lower() or 'which topic would you like to work on?' in content.lower():
            return 'waiting_for_topic'
        elif 'here are some topics available for this course:' in content.lower():
            return 'waiting_for_topic_selection'
        elif 'i\'m now generating a practice set for' in content.lower():
            return 'practice_ready'
        
        return 'start'
    
    def handle_case_1_step_1(self, available_courses: list[str]) -> str:
        """Case 1 - Step 1: 询问课程"""
        courses_text = ', '.join(available_courses)
        
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Great idea to work on your weak topics 😊
            </div>
            <div style="margin-bottom: 12px;">
                Before we start, which course would you like to practise?
            </div>
            <div style="margin-bottom: 12px;">
                Here are the courses you're currently enrolled in:
            </div>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                {courses_text}
            </div>
            <div>
                Please type the course name you want to practise.
            </div>
        </div>
        """
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def handle_case_2_step_1(self, mentioned_course: str, available_courses: list[str], account: StudentAccount) -> str:
        """Case 2 - Step 1: 处理用户指定的课程"""
        # 验证课程是否在学生课程列表中
        is_valid, valid_course = self.validate_course_input(mentioned_course, available_courses)
        
        if not is_valid:
            courses_text = ', '.join(available_courses)
            return f"""
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    I'm not seeing that course in your enrolments 🤔
                </div>
                <div style="margin-bottom: 12px;">
                    Please check the course name and try again.
                    These are the courses you're currently enrolled in:
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                    {courses_text}
                </div>
                <div>
                    Please type the course name you want to practise.
                </div>
            </div>
            """
        
        # 课程有效，获取主题列表
        topics = self.get_course_topics(valid_course)
        
        if not topics:
            return f"""
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    Got it, you'd like to practise {valid_course} 😊
                </div>
                <div style="margin-bottom: 12px;">
                    I don't see specific topics for this course yet. Let me generate general practice for you.
                </div>
                <button
                    class="cw-cta-btn"
                    onclick="window.startPracticeSession && window.startPracticeSession('{valid_course}')"
                    aria-label="Start general practice for {valid_course}"
                >
                    Start {valid_course} General Practice
                    <span style="margin-left: 8px;">→</span>
                </button>
            </div>
            """
        
        topics_text = '\n'.join([f"• {topic.title()}" for topic in topics[:10]])  # 限制显示前10个主题
        
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Got it, you'd like to practise {valid_course} 😊
            </div>
            <div style="margin-bottom: 12px;">
                Here are some topics available for this course:
            </div>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                {topics_text}
            </div>
            <div>
                Which topic would you like to work on?
                Please type the topic name you want to practise.
            </div>
        </div>
        """
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def handle_case_3_step_1(self, mentioned_topic: str, available_courses: list[str]) -> str:
        """Case 3 - Step 1: 用户指定了主题但没有课程"""
        courses_text = ', '.join(available_courses)
        
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Nice, that's a good topic to review 👍
            </div>
            <div style="margin-bottom: 12px;">
                To set things up correctly, which course is this topic for?
            </div>
            <div style="margin-bottom: 12px;">
                Here are the courses you're currently enrolled in:
            </div>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                {courses_text}
            </div>
            <div>
                Please type the course name you want to practise.
            </div>
        </div>
        """
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def handle_complete_selection(self, course: str, topic: str, account: StudentAccount) -> str:
        """处理完整的课程和主题选择"""
        available_courses = self.get_student_courses(account)
        is_valid_course, valid_course = self.validate_course_input(course, available_courses)
        
        if not is_valid_course:
            courses_text = ', '.join(available_courses)
            return f"""
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    I'm not seeing that course in your enrolments 🤔
                </div>
                <div style="margin-bottom: 12px;">
                    Please check the course name and try again.
                    These are the courses you're currently enrolled in:
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace;">
                    {courses_text}
                </div>
                <div>
                    Please type the course name you want to practise.
                </div>
            </div>
            """
        
        # 验证主题
        available_topics = self.get_course_topics(valid_course)
        is_valid_topic, valid_topic = self.validate_topic_input(topic, available_topics)
        
        if not is_valid_topic:
            topics_text = '\n'.join([f"• {t.title()}" for t in available_topics[:10]])
            return f"""
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    I'm not able to match that to a topic in this course 😅
                </div>
                <div style="margin-bottom: 12px;">
                    Please check the spelling and try again by choosing a topic from the list above.
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                    {topics_text}
                </div>
                <div>
                    Please type the topic name you want to practise.
                </div>
            </div>
            """
        
        # 生成练习
        return self.generate_practice_for_topic(valid_course, valid_topic)
    
    def generate_practice_for_topic(self, course: str, topic: str) -> str:
        """为特定课程和主题生成练习 - 复用现有的API逻辑"""
        print(f"[DEBUG] generate_practice_for_topic 被调用: course={course}, topic={topic}")
        
        # 返回"正在生成"消息，让前端处理实际的生成
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Great choice 💪
            </div>
            <div style="margin-bottom: 12px;">
                I'm now generating a practice set for {course} – {topic}.
                Please wait a moment…
            </div>
        </div>
        """
    
    def generate_welcome_response(self) -> str:
        """生成固定的欢迎回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                🌟 Hi there! I'm your AI Learning Coach — great to see you!
            </div>
            <div style="line-height: 1.6;">
                How are you feeling today? 😊
                <br /><br />
                I'm here to help you stay on track and feel confident about your studies.
                <br /><br />
                You can ask me about:
                <ul style="padding-left: 18px; margin: 8px 0;">
                    <li>Your study plan or schedule 🗓️</li>
                    <li>Practice exercises for tricky topics 💡</li>
                    <li>Or just ask for a little motivation and encouragement! 💬✨</li>
                </ul>
                Let's make today a productive one! 🚀
            </div>
        </div>
        """
    
    def validate_topic_input(self, user_input: str, available_topics: list[str]) -> tuple[bool, str]:
        """验证用户输入的主题是否有效"""
        user_input_clean = user_input.strip().lower()
        
        # 精确匹配（忽略大小写）
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # 包含匹配
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # 关键词匹配
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # 如果用户输入的词汇中有超过一半匹配主题词汇，则认为匹配
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None