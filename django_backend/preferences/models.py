# preferences/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from stu_accounts.models import StudentAccount

class StudentPreference(models.Model):

    student = models.OneToOneField(
        StudentAccount,
        to_field='student_id',   
        db_column='student_id', 
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

    avoid_days_bitmask = models.PositiveSmallIntegerField(default=0)  # 0..127
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'student_preferences' 

    def __str__(self):
        return f'CurrentPref<{self.student_id}>'


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
