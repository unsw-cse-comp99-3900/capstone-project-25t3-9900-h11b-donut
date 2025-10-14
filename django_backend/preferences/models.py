# preferences/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import StudentAccount

class StudentPreference(models.Model):
    """
    当前偏好（每个学生最多一条）
    主键=student_id(与 StudentAccount 一对一)
    """
    student = models.OneToOneField(
        StudentAccount,
        to_field='student_id',   # 绑定到 StudentAccount.student_id
        db_column='student_id',  # 复用列名为 student_id
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='pref_current',
    )
    daily_hours = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0.25), MaxValueValidator(24)]
    )
    weekly_study_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    # 0..6 表示周日..周六的 bitmask
    avoid_days_bitmask = models.PositiveSmallIntegerField(default=0)  # 0..127
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'student_preferences'  # 表名可按需改

    def __str__(self):
        return f'CurrentPref<{self.student_id}>'

    # 便捷属性：数组 <-> bitmask（可选用）
    @property
    def avoid_days(self):
        return [d for d in range(7) if (self.avoid_days_bitmask >> d) & 1]

    @avoid_days.setter
    def avoid_days(self, days):
        mask = 0
        for d in (days or []):
            d = int(d)
            if 0 <= d <= 6:
                mask |= (1 << d)
        self.avoid_days_bitmask = mask


class StudentPreferenceDefault(models.Model):
    """
    默认偏好（勾“Save as default”时写/更新这里）
    主键=student_id（与 StudentAccount 一对一）
    """
    student = models.OneToOneField(
        StudentAccount,
        to_field='student_id',
        db_column='student_id',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='pref_default',
    )
    daily_hours = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0.25), MaxValueValidator(24)]
    )
    weekly_study_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    avoid_days_bitmask = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'student_preferences_default'

    def __str__(self):
        return f'DefaultPref<{self.student_id}>'

    @property
    def avoid_days(self):
        return [d for d in range(7) if (self.avoid_days_bitmask >> d) & 1]

    @avoid_days.setter
    def avoid_days(self, days):
        mask = 0
        for d in (days or []):
            d = int(d)
            if 0 <= d <= 6:
                mask |= (1 << d)
        self.avoid_days_bitmask = mask
