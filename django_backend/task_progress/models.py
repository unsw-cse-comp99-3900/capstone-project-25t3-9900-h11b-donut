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