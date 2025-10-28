from django.db import models

# 课程目录：用于搜索/展示
class CourseCatalog(models.Model):
    code = models.CharField(max_length=16, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    illustration = models.CharField(max_length=32, default="orange")  #orange|student|admin

    class Meta:
        db_table = "course_catalog"

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


# 课程任务：课程内的发布任务
class CourseTask(models.Model):
    id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=16)  # 直接存课程代码，Sprint1 简化
    title = models.CharField(max_length=255)
    deadline = models.DateField()
    brief = models.TextField(blank=True)
    percent_contribution = models.PositiveIntegerField(default=0)
    url = models.CharField(max_length=512, blank=True, null=True)
    class Meta:
        db_table = "course_task"

    def __str__(self) -> str:
        return f"{self.course_code} - {self.title}"


# 学生选课
class StudentEnrollment(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    course_code = models.CharField(max_length=16)

    class Meta:
        db_table = "student_enrollment"
        unique_together = ("student_id", "course_code")


# 任务进度（按学生-任务）
class TaskProgress(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    task_id = models.PositiveIntegerField()
    progress = models.PositiveIntegerField(default=0)  # 0..100

    class Meta:
        db_table = "task_progress"
        unique_together = ("student_id", "task_id")


# 学习材料（保持不变：与课程关联并提供下载）
class Material(models.Model):
    course_code = models.CharField(max_length=16)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1024)  # 可为后端下载路径或外链

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

    # 简答题答案（mcq 留空）
    short_answer = models.TextField(blank=True, null=True)

    # 关键词：先走 JSON，够用也好迁移
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
    # 不强制依赖 A/B/C/D，保留序号，label 可选
    label = models.CharField(max_length=2, blank=True, null=True)   # 'A'/'B'/'C'/'D'
    order = models.PositiveIntegerField(default=0)                  # 0..n
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