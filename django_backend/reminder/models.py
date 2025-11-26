from django.db import models
from courses.models import CourseTask
class Notification(models.Model):
    """
    System Alert Table
Used to store automatic messages for students (such as task deadline reminders, system announcements, etc.)
    """
    student_id = models.CharField(max_length=50, db_index=True)
    course_code = models.CharField(max_length=20, blank=True, null=True)
    task_id = models.IntegerField(blank=True, null=True)

    # Message type（due_alert, nightly_notice, system_notification and so on）
    message_type = models.CharField(max_length=32)

    # Display content
    title = models.CharField(max_length=200)
    preview = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    # Status field
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    # Time
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