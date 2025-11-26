
from django.db import models


class GeneratedQuestion(models.Model):

    TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('short_answer', 'Short Answer'),
    )
    
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=64, db_index=True)  # Generation session ID
    course_code = models.CharField(max_length=16, db_index=True)
    topic = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=10)
    

    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    question_data = models.JSONField()
    """
    MCQ format:
    {
        "question": "content",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "correct_answer": "A",
        "explanation": "explanation",
        "score": 10
    }
    
    Short Answer format:
    {
        "question": "content",
        "sample_answer": "sample answer",
        "grading_points": ["keypoint1", "keypoint2"],
        "score": 10
    }
    """

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

    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=64, db_index=True)
    student_id = models.CharField(max_length=64, db_index=True)
    question = models.ForeignKey(GeneratedQuestion, on_delete=models.CASCADE, related_name='answers')
    

    answer_text = models.TextField()
    

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
        "feedback": "feedback",
        "hint": "personalized hint",
        "solution": "full answer"
    }
    """
    

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
