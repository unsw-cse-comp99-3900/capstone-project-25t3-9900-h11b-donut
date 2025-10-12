from django.db import models
from accounts.models import StudentAccount

class StudentWeeklyPreference(models.Model):
    student = models.ForeignKey(StudentAccount, on_delete=models.CASCADE)
    semester_code = models.CharField(max_length=20)
    week_no = models.PositiveSmallIntegerField()
    daily_hours = models.DecimalField(max_digits=4, decimal_places=2)
    weekly_study_days = models.PositiveSmallIntegerField()
    avoid_days_bitmask = models.PositiveSmallIntegerField(default=0)
    mode = models.CharField(max_length=10, choices=[('manual', 'Manual'), ('default', 'Default')])
    derived_from_week_no = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_weekly_preferences'  # ✅ 复用原表
        unique_together = ('student', 'semester_code', 'week_no')

    def __str__(self):
        return f"{self.student.student_id} - Week {self.week_no} ({self.mode})"
