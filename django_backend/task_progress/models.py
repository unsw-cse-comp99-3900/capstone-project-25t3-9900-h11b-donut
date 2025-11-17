from django.db import models

# 任务进度（按学生-任务）
class TaskProgress(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    task_id = models.PositiveIntegerField()
    progress = models.PositiveIntegerField(default=0)  # 0..100
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task_progress"
        unique_together = ("student_id", "task_id")
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['task_id']),
        ]

    def __str__(self) -> str:
        return f"Student {self.student_id} - Task {self.task_id}: {self.progress}%"
    
class OverdueStudent(models.Model):
    """
    学生维度累计：某天“整天都未勾选”则 +1
    """
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64, unique=True)
    count_overdue = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "overdue_student"
        indexes = [
            models.Index(fields=["student_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id}: {self.count_overdue}"


class OverdueCourseStudent(models.Model):
    """
    学生×课程×任务维度累计：某天该 task 的所有 part 都未勾选则 +1（同日只加一次）
    """
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    course_code = models.CharField(max_length=32)
    #task_id = models.PositiveIntegerField()
    task_id = models.CharField(max_length=64)
    count_overdue = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "overdue_course_student"
        unique_together = ("student_id", "course_code", "task_id")
        indexes = [
            models.Index(fields=["student_id"]),
            models.Index(fields=["course_code"]),
            models.Index(fields=["task_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} / {self.course_code} / {self.task_id}: {self.count_overdue}"


class OverdueStudentDailyLog(models.Model):
    """
    去重日志（学生×日期）：用于防止同一天重复记账“整天未勾选”
    """
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    date = models.DateField()  # 以学生本地时区的自然日
    reason = models.CharField(max_length=128, blank=True, default="")  # 可选
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "overdue_student_daily_log"
        unique_together = ("student_id", "date")
        indexes = [
            models.Index(fields=["student_id"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"log[student={self.student_id}, date={self.date}]"


class OverdueTaskDailyLog(models.Model):
    """
    去重日志（学生×课程×任务×日期）：用于防止同一天对同一任务重复记账
    """
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    course_code = models.CharField(max_length=32)
    task_id = models.PositiveIntegerField()
    date = models.DateField()  # 以学生本地时区的自然日
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "overdue_task_daily_log"
        unique_together = ("student_id", "course_code", "task_id", "date")
        indexes = [
            models.Index(fields=["student_id"]),
            models.Index(fields=["course_code", "task_id"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"log[{self.student_id} / {self.course_code} / {self.task_id} @ {self.date}]"