from django.db import models
from courses.models import CourseTask
class Notification(models.Model):
    """
    系统提醒表
    用于存储学生的自动消息（例如任务截止提醒、系统公告等）
    """
    student_id = models.CharField(max_length=50, db_index=True)
    course_code = models.CharField(max_length=20, blank=True, null=True)
    task_id = models.IntegerField(blank=True, null=True)

    # 消息类型（due_alert, nightly_notice, system_notification 等）
    message_type = models.CharField(max_length=32)

    # 展示内容
    title = models.CharField(max_length=200)
    preview = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    # 状态字段
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    # 时间
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    due_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['student_id', 'message_type', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student_id', 'task_id', 'message_type'],
                name='uniq_notify'
            )
        ]

    def __str__(self):
        return f"{self.student_id} | {self.message_type} | {self.title[:30]}"


class DueReport(models.Model):



    student_id = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="student ID",
    )

  
    task = models.ForeignKey(
        CourseTask,
        on_delete=models.CASCADE,
        related_name="due_reports",
        db_index=True,
        verbose_name="course task",
        null=True,    
        blank=True,    
    )


    total_due_days = models.PositiveIntegerField(
        default=0,
        verbose_name="total due days",
    )


    consecutive_due_days = models.PositiveIntegerField(
        default=0,
        verbose_name="consecutive due days",
    )


    last_overdue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="last due date",
    )

    class Meta:
        db_table = "reminder_duereport"   
        unique_together = ("student_id", "task")

    def __str__(self):
        return (
            f"{self.student_id} / task={self.task_id} "
            f"(total={self.total_due_days}, consec={self.consecutive_due_days})"
        )