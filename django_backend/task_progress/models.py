from django.db import models

# Task Progress (by Student Task)
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
    Student dimension accumulation: If a day is not checked all day, then+1
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
    Student x Course x Task Dimension Cumulative: If all parts of the task are not checked on a certain day, then+1 (only added once on the same day)
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
   Duplicate log (student x date): used to prevent duplicate accounting on the same day "not checked all day"
    """
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    date = models.DateField()  # Based on the natural day in the student's local time zone
    reason = models.CharField(max_length=128, blank=True, default="")  # optional
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
        Duplicate log (student x course x task x date): used to prevent duplicate bookkeeping of the same task on the same day
    """
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    course_code = models.CharField(max_length=32)
    task_id = models.PositiveIntegerField()
    date = models.DateField()  
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