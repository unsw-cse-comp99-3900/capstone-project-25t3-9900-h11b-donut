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

# load var
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
            generation_config={"temperature": 0.7, "max_output_tokens": 2048}
        )
    except Exception as e:
        print(f"[DEBUG] Gemini fail to initialize: {e}")
        use_gemini = False

class AIChatService:
    """AI chat Service - Processing User Messages and Generating Intelligent Replies
"""
    
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
        """Obtain or create the user's conversation session"""
        # Create or obtain a temporary User object to be compatible with the existing model
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
        """Check whether a greeting message should be sent (currently handled by the front end based on session management)"""
        # Since the greeting logic is now entirely managed by the front end, this method can return a fixed value
        # Or, this method can be completely removed and let the front end make the decision directly.
        return False  # The front end now decides whether to send a greeting based on the session state.
    
    def detect_intent(self, message: str) -> str:
        """Detect the intent of the user's message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return 'general'
    
    def is_practice_request(self, message: str) -> bool:
        """Detect whether it is a practice request"""
        practice_keywords = [
            'practice', 'weak topic', 'difficult topic', 'need help with', 
            'don\'t understand', 'struggling with', 'weak in', 'find difficult',
            'bad at', 'want to practice', 'need practice', 'practice session'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in practice_keywords)
    
    def is_in_practice_flow(self, conversation_history: list[dict[str, Any]]) -> bool:
        """Check if it is in the practice process"""
        if not conversation_history:
            return False
        
        # Search for the latest AI news
        last_ai_message = None
        for msg in conversation_history:
            if msg['type'] == 'ai':
                last_ai_message = msg
                break
        
        if not last_ai_message:
            return False
        
        content = last_ai_message['content']
        
        # Check if there is a textual identifier indicating the practice process included.
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
        """Obtain the list of courses registered by the students"""
        try:
            from courses.models import StudentEnrollment
            enrollments = StudentEnrollment.objects.filter(student_id=account.student_id)
            return [enrollment.course_code for enrollment in enrollments]
        except Exception as e:
            print(f"[DEBUG] Failed to obtain student course information: {e}")
            return []
    
    def get_course_topics(self, course_code: str) -> list[str]:
        """Obtain the list of topic titles for the courses"""
        try:
            from courses.models import QuestionKeyword, QuestionKeywordMap
            topics = QuestionKeyword.objects.filter(
                questionkeywordmap__question__course_code=course_code
            ).values_list('name', flat=True).distinct()
            return list(topics)
        except Exception as e:
            print(f"[DEBUG] Failed to obtain the course topic: {e}")
            return []
    
    def validate_course_input(self, user_input: str, available_courses: list[str]) -> tuple[bool, str]:
        """Verify whether the course input by the user is valid"""
        user_input_clean = user_input.strip().upper()
        
        # Exact Match
        if user_input_clean in available_courses:
            return True, user_input_clean
        
        # Fuzzy matching (comparing after removing spaces)
        user_input_no_space = user_input_clean.replace(' ', '')
        for course in available_courses:
            if course.replace(' ', '') == user_input_no_space:
                return True, course
        
        # Partial match (if only part of the course code is entered)
        for course in available_courses:
            if user_input_clean in course or course in user_input_clean:
                return True, course
        
        return False, None
    
    # ==================== Learning plan question-answer status management method ====================
    
    def get_current_mode(self, user_id: str, get_sub_state: bool = False) -> str:
        """Obtain the current mode of the user"""
        from .models import StudyPlanQnAState
        
        try:
            state = StudyPlanQnAState.objects.get(student_id=user_id)
            if get_sub_state:
                return state.sub_state
            return state.current_mode
        except StudyPlanQnAState.DoesNotExist:
            # If there is no status record, return to the default mode.
            StudyPlanQnAState.objects.create(student_id=user_id, current_mode='general_chat', sub_state=None)
            return 'general_chat' if not get_sub_state else None
    
    def set_current_mode(self, user_id: str, mode: str, sub_state: str = None):
        """Set the current mode and sub-state of the user"""
        from .models import StudyPlanQnAState
        
        state, created = StudyPlanQnAState.objects.update_or_create(
            student_id=user_id,
            defaults={
                'current_mode': mode,
                'sub_state': sub_state
            }
        )
        
        if not created:
            state.current_mode = mode
            state.sub_state = sub_state
            state.save()
        
        print(f"[DEBUG] set mode: user={user_id}, mode={mode}, sub_state={sub_state}")
    
    def clear_mode(self, user_id: str):
        """Clear mode, return to general_chat"""
        from .models import StudyPlanQnAState
        
        try:
            state = StudyPlanQnAState.objects.get(student_id=user_id)
            state.current_mode = 'general_chat'
            state.sub_state = None
            state.save()
            print(f"[DEBUG] clear mode: user={user_id}")
        except StudyPlanQnAState.DoesNotExist:
            pass
    
    def is_explain_plan_request(self, message: str) -> bool:
        """Detect whether it is a request for an explanation of the learning plan"""
        explain_patterns = [
            r'explain.*plan',
            r'please.*explain.*plan',
            r'please.*explain.*study.*plan',
            r'tell.*about.*plan',
            r'plan.*explain',
            r'study.*plan.*explain',
            r'explain.*study.*plan'
        ]
        
        message_lower = message.lower()
        for pattern in explain_patterns:
            if re.search(pattern, message_lower):
                return True
        return False
    
    def is_stop_request(self, message: str) -> bool:
        """Detect whether it is a request to stop the current mode"""
        stop_patterns = [
            r'\bstop\b',
            r'\bexit\b', 
            r'\bback\b'
        ]
        
        message_lower = message.lower().strip()
        for pattern in stop_patterns:
            if re.search(pattern, message_lower):
                return True
        return False
    
    def is_why_plan_request(self, message: str) -> bool:
        """Detect whether it is a request to inquire about the overall reason of the plan"""
        why_patterns = [
            r'why.*plan',
            r'plan.*why',
            r'reason.*plan',
            r'plan.*reason'
        ]
        
        message_lower = message.lower()
        for pattern in why_patterns:
            if re.search(pattern, message_lower):
                return True
        return False
    
    def parse_explain_task_part_request(self, message: str) -> tuple[Optional[int], Optional[str]]:
        """Request for detailed explanation of a specific Task/Part"""
        # First, attempt to match the standard format "Explain Task X – Part Y"
        pattern = r'explain\s+task\s+(\d+)\s*[-–]\s*part\s+([A-Za-z])'
        match = re.search(pattern, message.lower())
        
        if match:
            task_num = int(match.group(1))
            part_letter = match.group(2).upper()
            return task_num, part_letter
        
        # If the standard format does not match, try to find a matching 'part' tag from the user's plan.
        # In this situation, it is necessary to obtain the user's plan data.
        # Here, return None. More complex matching is handled in the handle_study_plan_qna_mode.
        
        return None, None
    
    def find_part_by_label(self, message: str, plan_data: dict[str, Any]) -> Optional[tuple[int, str]]:
        """Search for the corresponding tasks and sections in the plan by using the labels."""
        message_lower = message.lower()
        
        aiSummary = plan_data.get('aiSummary', {})
        tasks = aiSummary.get('tasks', [])
        
        for task_idx, task in enumerate(tasks, 1):
            parts = task.get('parts', [])
            for part_idx, part in enumerate(parts):
                label = part.get('label', '').lower()
                detail = part.get('detail', '').lower()
                
                # Check whether the message contains the "part" label or detail.
                if label and label in message_lower:
                    part_letter = chr(65 + part_idx)  # A, B, C, ...
                    return task_idx, part_letter
                elif detail and any(word in detail for word in message_lower.split() if len(word) > 3):
                    part_letter = chr(65 + part_idx)
                    return task_idx, part_letter
        
        return None
    
    def get_current_plan_for_user(self, account: StudentAccount) -> Optional[dict[str, Any]]:
        """Obtain the user's current study plan"""
        return self.get_user_study_plan(account)
    
    def generate_explain_plan_welcome(self) -> str:
        """Generate a welcome message that enters the "explain my plan" mode."""
        return """<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        Of course, I'd be happy to explain your study plan. 😊
    </div>
    <div style="line-height: 1.6;">
        You can ask me about:
        <ol style="padding-left: 18px; margin: 8px 0;">
            <li>Why this plan was generated in this way, or</li>
            <li>The details of a specific task or part in your plan.</li>
        </ol>
        <div style="margin-bottom: 8px;">
            For example, you can say:
        </div>
        <ul style="padding-left: 18px; margin: 0 0 12px 0; font-style: italic;">
            <li>"Why did you give me this plan?"</li>
            <li>"Explain Task 1 - Part A."</li>
            <li>"Explain Task 1 - Part B."</li>
        </ul>
        If you want to go back to normal chat at any time, just type "stop".
    </div>
</div>"""
    
    def generate_why_plan_explanation(self, plan_data: dict[str, Any]) -> str:
        """Explain why this particular plan was devised in this way"""
        # Retrieve task information from aiSummary
        ai_summary = plan_data.get('aiSummary', {})
        tasks = ai_summary.get('tasks', [])
        
        # Constructing explanatory content
        explanation_parts = []
        
        # Title
        explanation_parts.append("""<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        Great question! 🌟
    </div>
    <div style="margin-bottom: 12px;">
        Here's why your study plan was designed this way:
    </div>""")
        
        # If there are tasks, display the explanations for each task.
        if tasks:
            explanation_parts.append("""<div style="margin-bottom: 16px;">""")
            
            for idx, task in enumerate(tasks, 1):
                task_title = task.get('taskTitle', f'Task {idx}')
                task_explanation = task.get('explanation', '')
                parts_count = len(task.get('parts', []))
                total_minutes = task.get('totalMinutes', 0)
                hours = total_minutes // 60
                mins = total_minutes % 60
                time_str = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
                
                # Task Card
                explanation_parts.append(f"""
    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; border-left: 3px solid #4CAF50;">
        <div style="font-weight: 600; margin-bottom: 6px;">📚 {task_title}</div>
        <div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">{parts_count} parts • {time_str} total</div>""")
                
                # Display the explanation of AI
                if task_explanation:
                    explanation_parts.append(f"""
        <div style="line-height: 1.5;">
            <strong>Why this breakdown:</strong><br/>
            {task_explanation}
        </div>""")
                
                explanation_parts.append("""
    </div>""")
            
            explanation_parts.append("""</div>""")
        else:
            # If there is no task data, display the general instructions.
            overall_reason = plan_data.get('overall_reason', 'This plan was designed to help you complete your assignments efficiently while balancing your workload.')
            explanation_parts.append(f"""
    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
        {overall_reason}
    </div>""")
        
        # Prompt the user to continue asking questions
        explanation_parts.append("""
    <div style="line-height: 1.6;">
        If you'd like more details, you can ask about a specific task or part, for example:
        <ul style="padding-left: 18px; margin: 8px 0; font-style: italic;">
            <li>"Explain Task 1 - Part A."</li>
            <li>"Explain Task 1 - Part B."</li>
        </ul>
        Or type "stop" if you want to go back to normal chat.
    </div>
</div>""")
        
        return ''.join(explanation_parts)
    
    def generate_task_part_explanation(self, plan_data: dict[str, Any], task_index: int, part_letter: str) -> str:
        """Generate the explanation for the specific Task/Part"""
        try:
            # Find the corresponding task and part from the planning data.
            ai_summary = plan_data.get('aiSummary', {})
            tasks = ai_summary.get('tasks', [])
            
            if task_index <= 0 or task_index > len(tasks):
                return self.generate_task_part_not_found(plan_data)
            
            task = tasks[task_index - 1]
            parts = task.get('parts', [])
            
            # Convert letters to indices (A=0, B=1, etc.)
            part_index = ord(part_letter) - ord('A')
            
            if part_index < 0 or part_index >= len(parts):
                return self.generate_task_part_not_found(plan_data)
            
            part = parts[part_index]
            part_label = part.get('label', f'Task {task_index} - Part {part_letter}')
            part_detail = part.get('detail', f'This part focuses on key concepts needed for {task.get("taskTitle", "this assignment")}.')
            part_why_in_plan = part.get('why_in_plan', 'This part builds foundational skills for the assignment.')
            
            return f"""<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        Sure! Let's look at {part_label}. ✏️
    </div>
    <div style="margin-bottom: 12px;">
        <div style="font-weight: 600; margin-bottom: 4px;">What this part is about:</div>
        <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; line-height: 1.6;">
            {part_detail}
        </div>
    </div>
    <div style="margin-bottom: 12px;">
        <div style="font-weight: 600; margin-bottom: 4px;">Why it appears in your plan at this time:</div>
        <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; line-height: 1.6;">
            {part_why_in_plan}
        </div>
    </div>
    <div style="line-height: 1.6;">
        In other words, this part helps you:
        <ul style="padding-left: 18px; margin: 8px 0;">
            <li>Build the skills you need for later parts of the assignment, and</li>
            <li>Make steady progress without leaving everything to the last minute.</li>
        </ul>
        <div style="margin-top: 12px;">
            You can continue asking about other parts or tasks, or type "stop" to go back to normal chat.
        </div>
    </div>
</div>"""
            
        except Exception as e:
            print(f"[DEBUG] Error occurred during the generation of task/part explanations: {e}")
            return self.generate_task_part_not_found(plan_data)
    
    def generate_task_part_not_found(self, plan_data: dict[str, Any]) -> str:
        """Generate a fallback message indicating that the corresponding Task/Part could not be found."""
        try:
            ai_summary = plan_data.get('aiSummary', {})
            tasks = ai_summary.get('tasks', [])
            
            # Create a task list
            task_list = []
            for i, task in enumerate(tasks, 1):
                task_name = task.get('taskTitle', f'Task {i}')
                parts = task.get('parts', [])
                part_list = []
                
                for j, part in enumerate(parts):
                    part_label = part.get('label', f'Part {chr(65 + j)}')
                    part_list.append(f'Part {chr(65 + j)} - {part_label}')
                
                task_list.append(f"{i}) Task {i} - {task_name}\n   " + "\n   ".join(f"• {part}" for part in part_list))
            
            tasks_text = "\n".join(task_list)
            
        except Exception:
            tasks_text = "No tasks found in your plan."
        
        return f"""<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        I'm not sure which part you mean. 🤔
    </div>
    <div style="margin-bottom: 12px;">
        Here are the tasks and parts in your current plan:
    </div>
    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-family: monospace; white-space: pre-line; line-height: 1.6;">
{tasks_text}
    </div>
    <div style="line-height: 1.6;">
        Please ask again using this format, for example:
        <ul style="padding-left: 18px; margin: 8px 0; font-style: italic;">
            <li>"Explain Task 1 - Part A."</li>
            <li>"Explain Task 1 - Part B."</li>
        </ul>
        Or type "stop" if you want to go back to normal chat.
    </div>
</div>"""
    
    def generate_no_plan_error(self) -> str:
        """Generate an error message indicating the absence of a study plan"""
        return """<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        I don't see an active study plan for you yet. 📋
    </div>
    <div style="line-height: 1.6;">
        To get a personalized explanation, please generate your study plan first from the "My Plan" section.
        <br /><br />
        Once you have a plan, I can explain:
        <ul style="padding-left: 18px; margin: 8px 0;">
            <li>Why tasks are scheduled in a specific order</li>
            <li>How deadlines and workload are balanced</li>
            <li>Tips for following your personalized schedule</li>
        </ul>
    </div>
</div>"""
    
    def generate_mode_exit_message(self) -> str:
        """Generate a confirmation message for the exit mode"""
        return """<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        No problem, we can switch back to normal chat. 😊
    </div>
    <div style="line-height: 1.6;">
        You can ask me anything about your studies, practice questions, or tasks now.
    </div>
</div>"""
    
    def handle_study_plan_qna_mode(self, account: StudentAccount, message: str) -> Optional[str]:
        """Handle user input in the question-and-answer mode of the study plan"""
        user_id = account.student_id
        current_sub_state = self.get_current_mode(user_id, get_sub_state=True)
        print(f"[DEBUG] handle_study_plan_qna_mode is called: user={user_id}, sub_state={current_sub_state}, message={message}")
        
        # First, check if it is a request for practice - if so, exit the explain mode and return None to allow the main process to handle it.
        if self.is_practice_request(message):
            print(f"[DEBUG] In the explain mode, a practice request was detected. Exit the explain mode.")
            self.clear_mode(user_id)
            return None  # Return None to allow process_message to reprocess this message
        
        # Check if it is a stop request
        if self.is_stop_request(message):
            self.clear_mode(user_id)
            return self.generate_mode_exit_message()
        
        # Obtain the user's plan data (required in many places)
        plan_data = self.get_current_plan_for_user(account)
        if not plan_data:
            self.clear_mode(user_id)
            return self.generate_no_plan_error()
        
        # Check to see if it is an inquiry about the overall cause
        if self.is_why_plan_request(message):
            # The status has been updated to "active".
            self.set_current_mode(user_id, 'study_plan_qna', 'active')
            return self.generate_why_plan_explanation(plan_data)
        
        # Check if it is an inquiry about a specific Task/Part (in the standard format)
        task_num, part_letter = self.parse_explain_task_part_request(message)
        if task_num and part_letter:
            # The status has been updated to "active".
            self.set_current_mode(user_id, 'study_plan_qna', 'active')
            return self.generate_task_part_explanation(plan_data, task_num, part_letter)
        
        # First, check if it is a general request for an explanation. Avoid matching it to a specific Part by mistake.
        explain_patterns = [
            r'\bexplain\b.*\bplan\b',
            r'\bplan\b.*\bexplain\b',
            r'tell.*about.*plan',
            r'how.*plan.*work'
        ]
        message_lower = message.lower()
        for pattern in explain_patterns:
            if re.search(pattern, message_lower):
                # This is a general request for explanation, and a welcome message will be returned.
                self.set_current_mode(user_id, 'study_plan_qna', 'active')
                return self.generate_explain_plan_welcome()
        
        # Try to find the matching part by using the tags (only when the specific content is explicitly mentioned)
        part_result = self.find_part_by_label(message, plan_data)
        if part_result:
            task_num, part_letter = part_result
            # The status has been updated to "active".
            self.set_current_mode(user_id, 'study_plan_qna', 'active')
            return self.generate_task_part_explanation(plan_data, task_num, part_letter)
        
        # If none of them match, return a friendly message.
        self.set_current_mode(user_id, 'study_plan_qna', 'active')
        return """<div>
    <div style="font-weight: 700; margin-bottom: 8px;">
        I'm not sure what you're asking about. 🤔
    </div>
    <div style="line-height: 1.6;">
        In this mode, you can ask me:
        <ul style="padding-left: 18px; margin: 8px 0;">
            <li>"Why did you give me this plan?" - to learn about the overall plan reasoning</li>
            <li>"Explain Task 1 - Part A." - to get details about a specific task part</li>
            <li>You can also mention specific part names like "HTML Fundamentals"</li>
        </ul>
        Or type "stop" to go back to normal chat.
    </div>
</div>"""

    # ==================== Practicing state management methods ====================
    
    def set_practice_setup_mode(self, user_id: str, step: str, course: str = None, topic: str = None, num_questions: int = None, difficulty: str = None):
        """Set practice mode"""
        from .models import PracticeSetupState
        
        state, created = PracticeSetupState.objects.update_or_create(
            student_id=user_id,
            defaults={
                'step': step,
                'course': course,
                'topic': topic,
                'num_questions': num_questions,
                'difficulty': difficulty
            }
        )
        
        if not created:
            state.step = step
            state.course = course
            state.topic = topic
            state.num_questions = num_questions
            state.difficulty = difficulty
            state.save()
        
        print(f"[DEBUG] Set the practice mode: user={user_id}, step={step}, course={course}, topic={topic}, num={num_questions}, diff={difficulty}")
    
    def get_practice_setup_state(self, user_id: str) -> Optional[dict[str, Any]]:
        """Obtain the status of the practice settings"""
        from .models import PracticeSetupState
        
        try:
            state = PracticeSetupState.objects.get(student_id=user_id)
            return {
                'step': state.step,
                'course': state.course,
                'topic': state.topic,
                'num_questions': state.num_questions,
                'difficulty': state.difficulty
            }
        except PracticeSetupState.DoesNotExist:
            return None
    
    def clear_practice_setup_mode(self, user_id: str):
        """Clear practice setting mode"""
        from .models import PracticeSetupState
        
        try:
            state = PracticeSetupState.objects.get(student_id=user_id)
            state.delete()
            print(f"[DEBUG] Clear the practice mode: user={user_id}")
        except PracticeSetupState.DoesNotExist:
            pass
    
    def is_in_practice_setup_mode(self, user_id: str) -> bool:
        """Check if it is in the practice setting mode"""
        from .models import PracticeSetupState
        
        return PracticeSetupState.objects.filter(student_id=user_id).exists()
    
    def handle_practice_setup_mode(self, account: StudentAccount, message: str) -> Optional[str]:
        """Handle user input in the practice setup mode"""
        user_id = account.student_id
        print(f"[DEBUG] handle_practice_setup_mode is called: user={user_id}, message={message}")
        state = self.get_practice_setup_state(user_id)
        
        if not state:
            return None
        
        # Check if "stop" has been entered - to exit the "practice" mode
        if message.strip().lower() == 'stop':
            self.clear_practice_setup_mode(user_id)
            return """
            <div>
                <div style="font-weight: 700; margin-bottom: 8px;">
                    No problem! 👍
                </div>
                <div style="margin-bottom: 12px;">
                    You've exited practice mode. Feel free to ask me anything else!
                </div>
            </div>
            """
        
        step = state['step']
        print(f"[DEBUG] current step: {step}")
        available_courses = self.get_student_courses(account)
        
        if step == 'course':
            # Handling course selection
            is_valid, validated_course = self.validate_course_input(message, available_courses)
            
            if is_valid:
                # The course is effective. Proceed to the topic selection step.
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
                        <div style="margin-bottom: 8px;">
                            Please type the topic name you want to practise.
                        </div>
                        <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                            Or type <strong>stop</strong> to return to normal chat.
                        </div>
                    </div>
                    """
                else:
                    # No topics found, clear mode and return error
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
                # Course invalid, show error and re-prompt
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
                    <div style="margin-bottom: 8px;">
                        Please type the course name you want to practise.
                    </div>
                    <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                        Or type <strong>stop</strong> to return to normal chat.
                    </div>
                </div>
                """
        
        elif step == 'topic':
            # Selecting the topic for processing
            course = state['course']
            topics = self.get_course_topics(course)
            print(f"[DEBUG] Topic verification: course={course}, available_topics={topics}, user_input={message}")
            is_valid, validated_topic = self.validate_topic_input(message, topics)
            print(f"[DEBUG] Topic verification Result: is_valid={is_valid}, validated_topic={validated_topic}")
            
            if is_valid:
                # The topic is valid. Proceed to the step of selecting the number of questions.
                self.set_practice_setup_mode(user_id, 'num_questions', course, validated_topic)
                return """
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        Great choice! 📚
                    </div>
                    <div style="margin-bottom: 12px;">
                        How many questions would you like to practice?
                    </div>
                    <div style="margin-bottom: 8px;">
                        Please enter a number (e.g., 5, 10, or 15)
                    </div>
                    <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                        Or type <strong>stop</strong> to return to normal chat.
                    </div>
                </div>
                """
            else:
                # Topic invalid, show error and re-prompt
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
                    <div style="margin-bottom: 8px;">
                        Please type the topic name you want to practise.
                    </div>
                    <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                        Or type <strong>stop</strong> to return to normal chat.
                    </div>
                </div>
                """
        
        elif step == 'num_questions':
            # Handle number of questions selection
            try:
                num = int(message.strip())
                if num < 1 or num > 50:
                    raise ValueError("Number out of range")
                
                # Number valid, proceed to difficulty selection step
                course = state['course']
                topic = state['topic']
                self.set_practice_setup_mode(user_id, 'difficulty', course, topic, num)
                return """
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        Perfect! 💪
                    </div>
                    <div style="margin-bottom: 12px;">
                        What difficulty level would you like?
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 12px; line-height: 1.6;">
                        • <strong>Easy</strong> - Basic concepts and fundamental questions<br>
                        • <strong>Medium</strong> - Moderate difficulty, requires good understanding<br>
                        • <strong>Hard</strong> - Challenging questions, tests deep knowledge
                    </div>
                    <div style="margin-bottom: 8px;">
                        Please type: <strong>easy</strong>, <strong>medium</strong>, or <strong>hard</strong>
                    </div>
                    <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                        Or type <strong>stop</strong> to return to normal chat.
                    </div>
                </div>
                """
            except (ValueError, TypeError):
                return """
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        Please enter a valid number 🤔
                    </div>
                    <div style="margin-bottom: 12px;">
                        The number should be between 1 and 50.
                    </div>
                    <div style="margin-bottom: 8px;">
                        How many questions would you like to practice?
                    </div>
                    <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                        Or type <strong>stop</strong> to return to normal chat.
                    </div>
                </div>
                """
        
        elif step == 'difficulty':
            # Difficulty level selection for processing
            difficulty_input = message.strip().lower()
            valid_difficulties = ['easy', 'medium', 'hard']
            
            if difficulty_input in valid_difficulties:
                # The difficulty level is appropriate. Generate the practice exercises.
                course = state['course']
                topic = state['topic']
                num_questions = state['num_questions']
                
                self.clear_practice_setup_mode(user_id)  # Clear the settings mode
                return self.generate_practice_for_topic(course, topic, num_questions, difficulty_input)
            else:
                return """
                <div>
                    <div style="font-weight: 700; margin-bottom: 8px;">
                        Please choose a valid difficulty level 😅
                    </div>
                    <div style="margin-bottom: 8px;">
                        Please type one of: <strong>easy</strong>, <strong>medium</strong>, or <strong>hard</strong>
                    </div>
                    <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                        Or type <strong>stop</strong> to return to normal chat.
                    </div>
                </div>
                """
        
        elif step == 'generating':
            # Already in generating phase, clear mode
            self.clear_practice_setup_mode(user_id)
            return None
        
        return None
    

    

    

    
    def extract_course_and_topic_from_message(self, message: str, available_courses: list[str]) -> tuple[str, str]:
        """Extract course and topic information from message"""
        # Extract course
        course = None
        for course_code in available_courses:
            if course_code.lower() in message.lower():
                course = course_code
                break
        
        # Extract topic (use existing weak topic extraction logic)
        topic = self.extract_weak_topic(message)
        
        return course, topic
    
    def get_user_study_plan(self, account: StudentAccount) -> Optional[dict[str, Any]]:
        """Get user's current study plan"""
        try:
            # Create temporary User object for query
            user, _ = User.objects.get_or_create(  # type: ignore
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()  # type: ignore
            return plan.plan_data if plan else None
        except Exception:
            return None
    
    def generate_plan_explanation(self, account: StudentAccount) -> str:
        """Generate study plan explanation"""
        plan_data = self.get_user_study_plan(account)
        
        if not plan_data:
            return """<div><div style="font-weight: 700; margin-bottom: 8px;">I don't see an active study plan for you yet. 📋</div><div style="line-height: 1.6;">To get a personalized explanation, please generate your study plan first from the "My Plan" section.<br /><br />Once you have a plan, I can explain:<ul style="padding-left: 18px; margin: 8px 0;"><li>Why tasks are scheduled in a specific order</li><li>How deadlines and workload are balanced</li><li>Tips for following your personalized schedule</li></ul></div></div>"""
        
        # Extract plan information
        ai_summary = plan_data.get('aiSummary', {})
        tasks = ai_summary.get('tasks', [])
        
        # Build explanation content - use more compact format
        explanation_parts = []
        
        # Overall description
        explanation_parts.append("""<div><div style="font-weight: 700; margin-bottom: 8px;">Hi! Here's a detailed explanation of your personalized learning plan. ✨</div>""")
        
        # Plan creation logic
        explanation_parts.append("""<div style="font-weight: 600; margin-bottom: 4px;">How your plan was created:</div><ul style="padding-left: 18px; margin: 0;"><li><strong>Course analysis:</strong> AI analyzed all your course requirements and deadlines</li><li><strong>Task breakdown:</strong> Each assignment was intelligently split into manageable parts</li><li><strong>Time allocation:</strong> Hours distributed based on task complexity and your preferences</li><li><strong>Schedule optimization:</strong> Tasks arranged to avoid conflicts and maintain steady progress</li></ul>""")
        
        # Task details
        if tasks:
            explanation_parts.append(f"""<div style="font-weight: 600; margin: 8px 0 4px;">Your plan includes {len(tasks)} main tasks:</div><ul style="padding-left: 18px; margin: 0;">""")
            
            for idx, task in enumerate(tasks, 1):  # Display all tasks and add index
                task_title = task.get('taskTitle', 'Unknown Task')
                task_explanation = task.get('explanation', '')  # 🔑 Get AI's explanation
                parts_count = len(task.get('parts', []))
                total_minutes = task.get('totalMinutes', 0)
                hours = total_minutes // 60
                mins = total_minutes % 60
                
                # Format time display
                time_str = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
                
                # Task card start
                explanation_parts.append(f"""<li style="margin-bottom: 12px;"><strong>{task_title}:</strong> {parts_count} parts, {time_str} total""")
                
                # 🔑 Display AI's explanation - this is key!
                if task_explanation:
                    explanation_parts.append(f"""<br/><div style="margin-top: 6px; padding: 8px; background: #e8f5e9; border-radius: 4px; font-size: 0.95em; line-height: 1.5;"><strong>📋 Why this breakdown:</strong><br/>{task_explanation}</div>""")
                
                explanation_parts.append("</li>")
            
            explanation_parts.append("</ul>")
        
        # usage tips
        explanation_parts.append("""<div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 6px;"><div style="font-weight: 600; margin-bottom: 4px;">💡 Pro Tips:</div><div>• Your plan automatically adapts if you miss a day<br/>• Each task is broken into focused work sessions<br/>• Ask me about specific parts for detailed guidance!</div></div></div>""")
        
        return ''.join(explanation_parts)
    
    def generate_task_help(self, message: str, account: StudentAccount) -> str:
        """Generate task help response"""
        plan_data = self.get_user_study_plan(account)
        
        # Try to extract task and part information from message
        part_match = re.search(r'part\s*(\d+)', message.lower())
        part_number = part_match.group(1) if part_match else "2"
        
        # If there is plan data, try to find relevant task
        if plan_data and plan_data.get('aiSummary', {}).get('tasks'):
            tasks = plan_data['aiSummary']['tasks']
            if tasks:
                # Use first task as example
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
        
        # Default reply
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
        """Verify whether the inputted topic by the user is valid"""
        user_input_clean = user_input.strip().lower()
        
        # Exact match (case insensitive)
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # Including matching
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # Keyword matching
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # If more than half of the words input by the user match the topic words, then a match is considered.
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def generate_encouragement(self) -> str:
        """Generate encouraging response"""
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
        """Extract the weak points from the message"""
        import re
        
        # Try various modes to match specific topics
        topic_patterns = [
            r'(?:weak.*in|struggling.*with|difficulty.*with|薄弱.*在|困难.*在|不擅长|不太会|搞不懂)\s*([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            r'(?:topic|主题|方面|领域)\s*[:：]?\s*([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            r'(?:help.*with|help.*me.*with|需要.*帮助|帮我.*?)([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            r'(?:find.*difficult|find.*challenging|find.*hard)\s+([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            # New mode: Directly match the topic name (for conversational selection)
            r'(?:want.*practice|need.*help|practice|help)\s+(?:with\s+)?([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))',
            # Match the individual topic names
            r'^([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort|mining|classification|clustering|unsupervised|supervised|regression|decision|tree|kmeans|pca|apriori))$'
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).strip()
        
        return None
    
    def extract_topic_from_response(self, message: str, available_topics: list[str]) -> str:
        """Extract the topic name from the user responses"""
        import re
        
        message_lower = message.lower().strip()
        
        # First, attempt an exact match
        for topic in available_topics:
            if topic.lower() in message_lower:
                return topic
        
        # Try fuzzy matching
        for topic in available_topics:
            topic_words = topic.lower().split()
            for word in topic_words:
                if len(word) > 3 and word in message_lower:  # Match words with a length greater than 3
                    return topic
        
        return None
    
    def extract_course_from_message(self, message: str) -> str:
        """Extract the course code from the message"""
        import re
        
        # Course code format - Extended mode to accommodate more expressions
        course_patterns = [
            r'(?:course|课程)\s*([A-Z]{4}\d{4})',
            r'([A-Z]{4}\d{4})\s*(?:course|课程)?',
            r'(?:in|for|about)\s+([A-Z]{4}\d{4})',
            r'(?:help.*with|practice|study|learn|need.*help)\s+([A-Z]{4}\d{4})',
            r'([A-Z]{4}\d{4})(?:\s+|$)',  # Match the independent course codes
        ]
        
        for pattern in course_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).upper()
        
        return None
    
    def generate_course_topic_selection(self, course_code: str) -> str:
        """Generate course topic selection interface - in a conversational format, applicable to any course"""
        try:
            from courses.models import Question, QuestionKeyword
            from django.db.models import Count
            
            # Obtain all the keywords and the number of questions for this course
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
            
            # Constructing a topic list - in a conversational format
            topic_list = ""
            for i, keyword in enumerate(course_keywords, 1):
                topic_name = keyword.name
                question_count = keyword.question_count
                topic_list += f"{i}. {topic_name.title()} ({question_count} questions)\n"
            
            # Obtain the first topic as an example
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
        """Check whether the topic is specific enough"""
        if not topic or len(topic) < 3:
            return False
        
        # Check if it contains technical keywords
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
        
        # Eliminate overly vague expressions
        vague_terms = ['everything', 'anything', 'something', 'stuff', 'things', 'all', 'general']
        is_vague = any(term in topic.lower() for term in vague_terms)
        
        return has_technical_keyword and not is_vague
    
    def generate_practice_response(self, topic: str = None) -> str:
        """Generate practice suggestion reply"""
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
        """Generate a reply to the clarification request"""
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
        """Verify whether the inputted topic by the user is valid"""
        user_input_clean = user_input.strip().lower()
        
        # Exact match (case insensitive)
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # Including matching
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # Keyword matching
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # If more than half of the words input by the user match the topic words, then a match is considered.
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def generate_greeting_response(self) -> str:
        """Generate a greeting reply"""
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
        """Verify whether the inputted topic by the user is valid"""
        user_input_clean = user_input.strip().lower()
        
        # Exact match (case insensitive)
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # Including matching
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # Keyword matching
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # If more than half of the words input by the user match the topic words, then a match is considered.
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def generate_general_response(self) -> str:
        """Generate a general response"""
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
        """Verify whether the inputted topic by the user is valid"""
        user_input_clean = user_input.strip().lower()
        
        # Exact match (case insensitive)
        for topic in available_topics:
            if topic.lower() == user_input_clean:
                return True, topic
        
        # Including matching
        for topic in available_topics:
            if user_input_clean in topic.lower() or topic.lower() in user_input_clean:
                return True, topic
        
        # Keyword matching
        user_words = user_input_clean.split()
        for topic in available_topics:
            topic_words = topic.lower().split()
            # If more than half of the words input by the user match the topic words, then a match is considered.
            matches = sum(1 for word in user_words if word in topic_words)
            if matches >= min(2, len(user_words), len(topic_words)):
                return True, topic
        
        return False, None
    
    def generate_ai_response(self, message: str, account: StudentAccount, conversation_history: Optional[list[dict[str, Any]]] = None) -> str:
        """Use Gemini AI to generate intelligent responses"""
        if not use_gemini:
            # If there were no AI, we would revert to rule-based responses.
            intent = self.detect_intent(message)
            if intent == 'explain_plan':
                return self.generate_plan_explanation(account)
            elif intent == 'task_help':
                return self.generate_task_help(message, account)
            elif intent == 'encouragement':
                return self.generate_encouragement()
            elif intent == 'practice':
                # Check if specific courses are mentioned
                course_code = self.extract_course_from_message(message)
                if course_code:
                    return self.generate_course_topic_selection(course_code)
                else:
                    # Check for the presence of clearly defined weak points or themes
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
            # Import the necessary models
            from courses.models import StudentEnrollment, CourseCatalog, CourseTask
            from task_progress.models import TaskProgress
            from .models import RecentPracticeSession
            
            # Obtain the user's course selection information
            courses_context = ""
            try:
                enrollments = StudentEnrollment.objects.filter(student_id=account.student_id)  # type: ignore
                if enrollments.exists():
                    courses_list = []
                    for enrollment in enrollments[:5]:  # At most 5 courses
                        try:
                            course = CourseCatalog.objects.get(code=enrollment.course_code)  # type: ignore
                            courses_list.append(f"{course.code}: {course.title}")
                        except CourseCatalog.DoesNotExist:  # type: ignore
                            courses_list.append(enrollment.course_code)
                    if courses_list:
                        courses_context = f"\n\nEnrolled courses ({len(courses_list)}):\n- " + "\n- ".join(courses_list)
            except Exception as e:
                print(f"[DEBUG] Failed to obtain course selection information: {e}")
            
            # Obtain the user's task progress information
            tasks_context = ""
            try:
                # Obtain the progress of all tasks
                task_progresses = TaskProgress.objects.filter(student_id=account.student_id).order_by('-updated_at')[:10]  # type: ignore
                if task_progresses.exists():
                    tasks_info = []
                    for tp in task_progresses[:5]:  # Show at most 5 recently updated tasks
                        try:
                            task = CourseTask.objects.get(id=tp.task_id)  # type: ignore
                            status = "✓ Complete" if tp.progress >= 100 else f"⏳ {tp.progress}% done"
                            tasks_info.append(f"{task.course_code} - {task.title}: {status}")
                        except CourseTask.DoesNotExist:  # type: ignore
                            pass
                    if tasks_info:
                        tasks_context = f"\n\nRecent task progress:\n- " + "\n- ".join(tasks_info)
            except Exception as e:
                print(f"[DEBUG] Failed to obtain the task progress: {e}")
            
            # Obtain the latest practice test results
            practice_context = ""
            try:
                recent_session = RecentPracticeSession.get_latest_session(account.student_id)  # type: ignore
                if recent_session:
                    practice_context = f"\n\n🎯 Most recent practice test:"
                    practice_context += f"\n- Course: {recent_session.course_code}"
                    practice_context += f"\n- Topic: {recent_session.topic}"
                    practice_context += f"\n- Score: {recent_session.total_score}/{recent_session.max_score} ({recent_session.percentage:.1f}%)"
                    practice_context += f"\n- Questions: {recent_session.questions_count}"
                    
                    # Add detailed information for all the questions (no limit on the number)
                    test_data = recent_session.test_data
                    if test_data and 'questions' in test_data:
                        wrong_questions = [q for q in test_data['questions'] if not q.get('is_correct', True)]
                        if wrong_questions:
                            practice_context += f"\n- Wrong answers: {len(wrong_questions)} question(s)"
                            practice_context += "\n\nDetailed test results (ALL questions for student reference):"
                            # Display all questions without truncating the content
                            for idx, q in enumerate(test_data['questions'], 1):
                                status = "✓" if q.get('is_correct', False) else "✗"
                                practice_context += f"\n  Q{idx} [{status}]: {q.get('question_text', 'N/A')}"
                                
                                #If it is a multiple-choice question, display the options.
                                if q.get('question_type') == 'mcq' and q.get('options'):
                                    practice_context += f"\n      Options: {', '.join(q.get('options', []))}"
                                
                                practice_context += f"\n      Student's answer: {q.get('student_answer', 'N/A')}"
                                
                                if not q.get('is_correct', True):
                                    practice_context += f"\n      Correct answer: {q.get('correct_answer', 'N/A')}"
                                    if q.get('feedback'):
                                        practice_context += f"\n      Feedback: {q.get('feedback', '')}"
            except Exception as e:
                print(f"[DEBUG] Failed to obtain the practice test results: {e}")
            
            # Obtain the user's learning plan information
            plan_data = self.get_user_study_plan(account)
            plan_context = ""
            if plan_data:
                ai_summary = plan_data.get('aiSummary', {})
                tasks = ai_summary.get('tasks', [])
                if tasks:
                    plan_context = f"\n\nAI-generated study plan includes {len(tasks)} tasks: "
                    for task in tasks[:3]:  # Only the first three tasks are included.
                        task_title = task.get('taskTitle', 'Unknown Task')
                        parts_count = len(task.get('parts', []))
                        plan_context += f"\n- {task_title} ({parts_count} parts)"
            
            # Build the context of the conversation history - increase to 20 items
            history_context = ""
            if conversation_history:
                recent_messages = conversation_history[-20:]  # The latest 20 pieces of news (an increase from 6)
                history_context = "\n\nRecent conversation:\n"
                for msg in recent_messages:
                    role = "Student" if msg['type'] == 'user' else "Coach"
                    content = msg['content'][:200]  # Limit the length.
                    history_context += f"{role}: {content}\n"
            
            # Build AI prompts
            system_prompt = f"""You are an AI Learning Coach helping university students with their studies. You are supportive, encouraging, and provide practical advice.

Your role:
- Help students understand their study plans and assignments
- Provide guidance on specific tasks and parts
- Offer encouragement when students feel overwhelmed
- Suggest practice exercises for difficult topics
- Answer questions about academic work
- Use the student's course enrollment and task progress information to give personalized advice
- **IMPORTANT**: Help students understand their practice test results

Guidelines:
- Be warm, supportive, and encouraging
- Provide specific, actionable advice based on their actual courses and tasks
- Keep responses concise and helpful (max 300 words)
- Use a friendly, conversational tone
- Include relevant emojis to make responses more engaging
- Respond in plain text format, no HTML or markdown
- Address the student naturally without always using their name, or use their actual name if needed: {account.name or 'there'}
- When discussing tasks or courses, reference their actual enrolled courses and current progress

**When student asks about their practice test (e.g., "What questions did I get wrong?"):**
- Give a brief, encouraging summary of their test (score, topic)
- List the question numbers they got wrong in a simple format (e.g., "You got Q2, Q3, and Q5 incorrect")
- DO NOT explain each question in detail automatically
- Instead, invite them to ask about specific questions: "Which question would you like me to help you understand better?"
- Keep the initial response SHORT and conversational

**When student asks about a SPECIFIC question (e.g., "Can you explain Q2?" or "Help me with question 3"):**
- NOW provide a detailed explanation for THAT specific question:
  1. What they answered vs. the correct answer
  2. WHY their answer was incorrect
  3. WHY the correct answer is right (with clear conceptual explanation)
  4. A helpful tip for similar questions
- Be thorough but focus only on the question they asked about
- After explaining, ask if they'd like help with another question

Student context:
- Student ID: {account.student_id}
- Name: {account.name or 'Student'}{courses_context}{tasks_context}{practice_context}{plan_context}{history_context}

Current student message: {message}

Respond as their AI Learning Coach. Use the student's actual course, task, and practice test information to provide personalized, relevant advice. Keep responses concise unless student asks for detailed explanation of a specific question. Do not use "Test Student" - address them naturally or by their actual name."""
            # Call Gemini AI
            response = _model.generate_content(system_prompt)
            
            if response and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    ai_text = ""
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            ai_text += part.text
                    
                    if ai_text.strip():
                        # Remove HTML tags and Markdown formatting from AI responses
                        cleaned_text = self.clean_ai_response(ai_text)
                        return cleaned_text
            
            # If the AI reply fails, revert to the rule-based reply.
            return self.generate_general_response()
            
        except Exception as e:
            print(f"[DEBUG] AI reply generation failed: {e}")
            # Return to rule-based responses
            return self.generate_general_response()
    
    def process_message(self, account: StudentAccount, message: str) -> dict[str, Any]:
        """Process user messages and generate AI responses"""
        try:
            # Obtain or create a conversation session
            conversation = self.get_or_create_conversation(account)
            
            # Retrieve conversation history for context - Increase to 30 entries to provide more context
            conversation_history = self.get_conversation_history(account, limit=30)
            
            # Check if it is a welcome message (an automatically sent initialization message)
            if message.lower().strip() == 'welcome':
                # For the welcome message, no user messages are saved; only the AI's welcome response is returned.
                ai_response = self.generate_welcome_response()
                
                # Save the AI response
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
            
            # For the users' genuine messages, they will be processed normally.
            # Save user messages
            print(f"[DEBUG] Save user messages to the database: user={account.student_id}, message={message}")
            user_message = ChatMessage.objects.create(  # type: ignore
                conversation=conversation,
                message_type='user',
                content=message
            )
            print(f"[DEBUG] The user message has been saved, ID: {user_message.id}")
            
            # Update the final activity time of the conversation
            from django.utils import timezone
            conversation.last_activity_at = timezone.now()
            conversation.save()
            
            # 获取当前用户模式
            current_mode = self.get_current_mode(account.student_id)
            print(f"[DEBUG] 当前用户模式: {current_mode}")
            
            # 优先级1: 检查是否是显式模块触发词
            if self.is_explain_plan_request(message) and current_mode != 'study_plan_qna':
                # 进入study_plan_qna模式
                self.set_current_mode(account.student_id, 'study_plan_qna', 'awaiting_question')
                ai_response = self.generate_explain_plan_welcome()
                intent = 'study_plan_qna'
            elif self.is_practice_request(message) and current_mode != 'practice_setup':
                # 检查是否是练习请求,如果是,启动练习设置模式
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
                            <div style="margin-bottom: 12px;">
                                Please type the course name you want to practise.
                            </div>
                            <div style="font-size: 13px; color: #6c757d; font-style: italic;">
                                Or type <strong>stop</strong> to return to normal chat.
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
                intent = 'practice'
            # 优先级2: 检查是否在特定模式中
            elif current_mode == 'study_plan_qna':
                # 在study_plan_qna模式中，使用专门的处理逻辑
                ai_response = self.handle_study_plan_qna_mode(account, message)
                if ai_response is None:
                    # 🔑 如果返回None，说明检测到了其他请求(如practice)，需要重新处理
                    # 重新检测意图并处理
                    if self.is_practice_request(message):
                        # 处理练习请求
                        available_courses = self.get_student_courses(account)
                        mentioned_course, mentioned_topic = self.extract_course_and_topic_from_message(message, available_courses)
                        
                        if mentioned_course and mentioned_topic:
                            # 验证课程和主题
                            is_course_valid, valid_course = self.validate_course_input(mentioned_course, available_courses)
                            if is_course_valid:
                                topics = self.get_course_topics(valid_course)
                                is_topic_valid, valid_topic = self.validate_topic_input(mentioned_topic, topics)
                                
                                if is_topic_valid:
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
                        else:
                            # 没有提供课程和主题,启动练习设置模式
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
                        intent = 'practice'
                    else:
                        # 其他情况，使用通用回复
                        intent = self.detect_intent(message)
                        ai_response = self.generate_general_response()
                else:
                    intent = 'study_plan_qna'
            elif self.is_in_practice_setup_mode(account.student_id):
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
                # 普通模式：根据意图生成回复
                intent = self.detect_intent(message)
                
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
            # 确保User和StudentAccount一致
            user, created = User.objects.get_or_create(  # type: ignore
                username=account.student_id,
                defaults={
                    'email': account.email or f'{account.student_id}@temp.com',
                    'first_name': account.name if account.name else f'Student {account.student_id}'
                }
            )
            
            if created:
                print(f"[DEBUG] create new Django User: {user.username} for StudentAccount: {account.student_id}")
            else:
                # 确保现有User的email与StudentAccount同步
                if account.email and user.email != account.email:
                    user.email = account.email
                    user.save()
                    print(f"[DEBUG] 同步了User email: {user.email}")
                    
            print(f"[DEBUG] save plan - StudentAccount: {account.student_id} -> Django User: {user.username}")
            
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
        elif 'i'm now generating a practice set for' in content.lower():
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
    
    def generate_practice_for_topic(self, course: str, topic: str, num_questions: int = 5, difficulty: str = 'medium') -> str:
        """为特定课程和主题生成练习 - 复用现有的API逻辑"""
        print(f"[DEBUG] generate_practice_for_topic 被调用: course={course}, topic={topic}, num={num_questions}, difficulty={difficulty}")
        
        # 返回"正在生成"消息，让前端处理实际的生成
        # 前端会收到这个消息，然后调用generate-practice API，并传递num_questions和difficulty参数
        return f"""
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Great choice 💪
            </div>
            <div style="margin-bottom: 12px;">
                I'm now generating {num_questions} {difficulty} questions for {course} – {topic}.
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