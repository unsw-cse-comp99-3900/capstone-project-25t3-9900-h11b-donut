from django.db import models


class CourseCatalog(models.Model):
    code = models.CharField(max_length=16, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    illustration = models.CharField(max_length=32, default="orange")  #orange|student|admin

    class Meta:
        db_table = "course_catalog"

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseTask(models.Model):
    id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=16)  
    title = models.CharField(max_length=255)
    # deadline = models.DateField()
    deadline = models.DateTimeField()
    
    brief = models.TextField(blank=True)
    percent_contribution = models.PositiveIntegerField(default=0)
    url = models.CharField(max_length=512, blank=True, null=True)
    class Meta:
        db_table = "course_task"

    def __str__(self) -> str:
        return f"{self.course_code} - {self.title}"



class StudentEnrollment(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    course_code = models.CharField(max_length=16)

    class Meta:
        db_table = "student_enrollment"
        unique_together = ("student_id", "course_code")


class Material(models.Model):
    course_code = models.CharField(max_length=16)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1024)

    class Meta:
        db_table = "material"

    def __str__(self) -> str:
        return f"{self.title}"
    
class Question(models.Model):
    TYPE_CHOICES = (
        ('mcq', 'Multiple Choice'),
        ('short', 'Short Answer'),
    )

    id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=16, db_index=True)

    qtype = models.CharField(max_length=10, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    text = models.TextField()


    short_answer = models.TextField(blank=True, null=True)

    keywords_json = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"[{self.course_code}][{self.qtype}] {self.title}"


class QuestionChoice(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='choices'
    )

    label = models.CharField(max_length=2, blank=True, null=True)  
    order = models.PositiveIntegerField(default=0)               
    content = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "question_choice"
        ordering = ["question_id", "order", "id"]
        indexes = [models.Index(fields=['question', 'order'])]
        unique_together = (('question', 'order'),)

    def __str__(self) -> str:
        return f"Q{self.question_id}#{self.order} ({'✓' if self.is_correct else ' '})"


class QuestionKeyword(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "question_keyword"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class QuestionKeywordMap(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    keyword = models.ForeignKey(QuestionKeyword, on_delete=models.CASCADE)

    class Meta:
        db_table = "question_keyword_map"
        unique_together = (('question', 'keyword'),)

    def __str__(self) -> str:
        return f"Q{self.question_id} <-> {self.keyword_id}"