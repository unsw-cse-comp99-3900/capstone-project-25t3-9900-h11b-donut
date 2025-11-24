from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ChatConversation(models.Model):
    """对话会话模型 - 存储用户的对话历史"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)  # 用户最后活动时间
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.user.username}"

class ChatMessage(models.Model):
    """聊天消息模型"""
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('ai', 'AI Response'),
    ]
    
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # 可选的结构化数据
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class UserStudyPlan(models.Model):
    """用户学习计划存储 - 用于AI对话中的计划解释"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    plan_data = models.JSONField()  # 存储完整的AI生成计划数据
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # 标记当前活跃的计划
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Study Plan for {self.user.username} - {self.created_at.date()}"
    
    @classmethod
    def cleanup_old_plans(cls):
        """清理7天前的旧计划"""
        cutoff_date = timezone.now() - timedelta(days=7)
        cls.objects.filter(created_at__lt=cutoff_date).delete()

class PracticeSetupState(models.Model):
    """练习设置状态模型 - 存储用户的练习流程状态"""
    student_id = models.CharField(max_length=20, unique=True)  # 学生ID
    step = models.CharField(max_length=20, choices=[
        ('course', 'Course Selection'),
        ('topic', 'Topic Selection'),
        ('num_questions', 'Number of Questions'),
        ('difficulty', 'Difficulty Selection'),
        ('generating', 'Generating Practice'),
    ])
    course = models.CharField(max_length=10, blank=True, null=True)  # 选择的课程
    topic = models.CharField(max_length=100, blank=True, null=True)  # 选择的主题
    num_questions = models.IntegerField(blank=True, null=True)  # 题目数量
    difficulty = models.CharField(max_length=20, blank=True, null=True)  # 难度等级: easy, medium, hard
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"PracticeSetup {self.student_id} - {self.step}"

class StudyPlanQnAState(models.Model):
    """学习计划问答状态模型 - 存储用户的学习计划解释流程状态"""
    student_id = models.CharField(max_length=20, unique=True)  # 学生ID
    current_mode = models.CharField(max_length=20, default='general_chat', choices=[
        ('general_chat', 'General Chat'),
        ('practice_setup', 'Practice Setup'),
        ('study_plan_qna', 'Study Plan Q&A'),
    ])
    sub_state = models.CharField(max_length=20, blank=True, null=True)  # 子状态，如awaiting_question
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"StudyPlanQnA {self.student_id} - {self.current_mode}"

# 自动清理旧数据的管理器
class ChatManager:
    @staticmethod
    def cleanup_old_conversations():
        """清理7天前的对话记录"""
        cutoff_date = timezone.now() - timedelta(days=7)
        ChatConversation.objects.filter(created_at__lt=cutoff_date).delete()

class RecentPracticeSession(models.Model):
    """最近的练习测试会话 - 用于AI聊天中引用学生的测试结果"""
    student_id = models.CharField(max_length=20, db_index=True)
    session_id = models.CharField(max_length=100)
    course_code = models.CharField(max_length=16)
    topic = models.CharField(max_length=255)
    
    # 测试结果摘要
    total_score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    questions_count = models.IntegerField(default=0)
    
    # 详细结果 (JSON格式存储题目、答案、得分等)
    test_data = models.JSONField(default=dict)
    # 格式: {
    #   "questions": [
    #     {
    #       "question_text": "...",
    #       "student_answer": "...",
    #       "correct_answer": "...",
    #       "score": 5,
    #       "max_score": 5,
    #       "feedback": "...",
    #       "is_correct": true
    #     },
    #     ...
    #   ]
    # }
    
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "recent_practice_session"
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['student_id', '-completed_at']),
        ]
    
    def __str__(self):
        return f"{self.student_id} - {self.course_code}/{self.topic} ({self.percentage:.1f}%)"
    
    @classmethod
    def get_latest_session(cls, student_id: str):
        """获取学生最近的一次测试会话"""
        try:
            return cls.objects.filter(student_id=student_id).first()
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def cleanup_old_sessions(cls, days=30):
        """清理30天前的旧测试记录"""
        cutoff_date = timezone.now() - timedelta(days=days)
        cls.objects.filter(completed_at__lt=cutoff_date).delete()