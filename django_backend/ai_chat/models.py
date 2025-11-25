from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ChatConversation(models.Model):
    """chat session model - stores the user's conversation history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)  
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.user.username}"

class ChatMessage(models.Model):
    """chat msg model"""
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('ai', 'AI Response'),
    ]
    
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # optional ds
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class UserStudyPlan(models.Model):
    """store the plan for ai explaination"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    plan_data = models.JSONField()  # save plan data
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # tag as current plan
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Study Plan for {self.user.username} - {self.created_at.date()}"
    
    @classmethod
    def cleanup_old_plans(cls):
        """clear old plan"""
        cutoff_date = timezone.now() - timedelta(days=7)
        cls.objects.filter(created_at__lt=cutoff_date).delete()

class PracticeSetupState(models.Model):
    """Practice Setting State Model - Store Users' Practice Process States"""
    student_id = models.CharField(max_length=20, unique=True)  # stu ID
    step = models.CharField(max_length=20, choices=[
        ('course', 'Course Selection'),
        ('topic', 'Topic Selection'),
        ('num_questions', 'Number of Questions'),
        ('difficulty', 'Difficulty Selection'),
        ('generating', 'Generating Practice'),
    ])
    course = models.CharField(max_length=10, blank=True, null=True)  # course
    topic = models.CharField(max_length=100, blank=True, null=True)  # topic
    num_questions = models.IntegerField(blank=True, null=True)  # number of questions
    difficulty = models.CharField(max_length=20, blank=True, null=True)  # difficulty level: easy, medium, hard
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"PracticeSetup {self.student_id} - {self.step}"

class StudyPlanQnAState(models.Model):
    """Learning Plan Q&A Status Model - Store User's Learning Plan Explanation Process Status"""
    student_id = models.CharField(max_length=20, unique=True)  # stu ID
    current_mode = models.CharField(max_length=20, default='general_chat', choices=[
        ('general_chat', 'General Chat'),
        ('practice_setup', 'Practice Setup'),
        ('study_plan_qna', 'Study Plan Q&A'),
    ])
    sub_state = models.CharField(max_length=20, blank=True, null=True)  # sub-status:awaiting_question
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"StudyPlanQnA {self.student_id} - {self.current_mode}"

# clear old data automatically
class ChatManager:
    @staticmethod
    def cleanup_old_conversations():
        
        cutoff_date = timezone.now() - timedelta(days=7)
        ChatConversation.objects.filter(created_at__lt=cutoff_date).delete()

class RecentPracticeSession(models.Model):
    """RecentPracticeSession - for students practice res"""
    student_id = models.CharField(max_length=20, db_index=True)
    session_id = models.CharField(max_length=100)
    course_code = models.CharField(max_length=16)
    topic = models.CharField(max_length=255)
    
    # summary for the test
    total_score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    questions_count = models.IntegerField(default=0)
    
    # details about res
    test_data = models.JSONField(default=dict)
    # format: {
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
        """get latest msg"""
        try:
            return cls.objects.filter(student_id=student_id).first()
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def cleanup_old_sessions(cls, days=30):
        """clear past 30 days data"""
        cutoff_date = timezone.now() - timedelta(days=days)
        cls.objects.filter(completed_at__lt=cutoff_date).delete()