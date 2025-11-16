"""
AI Question Generator Models
用于存储示例题目和生成的题目
"""
from django.db import models


class SampleQuestion(models.Model):
    """
    示例题目模板 - Admin上传，用于AI生成参考
    """
    TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('short_answer', 'Short Answer'),
    )
    
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    
    id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=16, db_index=True)
    topic = models.CharField(max_length=255, db_index=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    # 题目类型
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # 题目内容
    question_text = models.TextField()
    
    # 选择题字段
    options = models.JSONField(null=True, blank=True)  # ["A. ...", "B. ...", "C. ...", "D. ..."]
    correct_answer = models.CharField(max_length=10, null=True, blank=True)  # "A", "B", etc.
    explanation = models.TextField(null=True, blank=True)
    
    # 简答题字段
    sample_answer = models.TextField(null=True, blank=True)
    grading_points = models.JSONField(null=True, blank=True)  # ["要点1", "要点2", ...]
    
    # 分值
    score = models.IntegerField(default=10)
    
    # 元数据
    created_by = models.CharField(max_length=64, null=True, blank=True)  # admin_id
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ai_sample_question'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course_code', 'topic']),
            models.Index(fields=['topic', 'difficulty']),
        ]
    
    def __str__(self):
        return f"[{self.topic}] [{self.question_type}] {self.question_text[:50]}..."


class GeneratedQuestion(models.Model):
    """
    AI生成的题目 - 用于记录和复用
    """
    TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('short_answer', 'Short Answer'),
    )
    
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=64, db_index=True)  # 生成会话ID
    course_code = models.CharField(max_length=16, db_index=True)
    topic = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=10)
    
    # 题目类型
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # 题目内容（JSON格式存储完整题目数据）
    question_data = models.JSONField()
    """
    MCQ格式:
    {
        "question": "题目文本",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "correct_answer": "A",
        "explanation": "解释",
        "score": 10
    }
    
    Short Answer格式:
    {
        "question": "题目文本",
        "sample_answer": "参考答案",
        "grading_points": ["要点1", "要点2"],
        "score": 10
    }
    """
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_generated_question'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['course_code', 'topic']),
        ]
    
    def __str__(self):
        return f"[{self.session_id}] [{self.question_type}] {self.topic}"


class StudentAnswer(models.Model):
    """
    学生答案记录
    """
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=64, db_index=True)
    student_id = models.CharField(max_length=64, db_index=True)
    question = models.ForeignKey(GeneratedQuestion, on_delete=models.CASCADE, related_name='answers')
    
    # 学生答案
    answer_text = models.TextField()
    
    # 评分结果（JSON格式）
    grading_result = models.JSONField(null=True, blank=True)
    """
    {
        "score": 8.5,
        "max_score": 10,
        "is_correct": true,  // MCQ only
        "breakdown": {  // Short answer only
            "Correctness": 4,
            "Completeness": 3,
            "Clarity": 2
        },
        "feedback": "详细反馈",
        "hint": "个性化提示",
        "solution": "完整解答"
    }
    """
    
    # 元数据
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_student_answer'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['session_id', 'student_id']),
            models.Index(fields=['student_id', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"[{self.student_id}] Session {self.session_id} Q{self.question_id}"
