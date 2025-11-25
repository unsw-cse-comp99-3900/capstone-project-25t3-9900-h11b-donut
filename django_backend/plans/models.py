from django.db import models
from django.utils import timezone


class StudyPlan(models.Model):

    id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=64, db_index=True)
    week_start_date = models.DateField() 
    week_offset = models.IntegerField(default=0)
    tz = models.CharField(max_length=64, default='Australia/Sydney')

    SOURCE_CHOICES = (
        ('ai', 'AI'),
        ('manual', 'Manual'),
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='ai')

    meta = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_plan"
        unique_together = ("student_id", "week_start_date")
        indexes = [
            models.Index(fields=["student_id", "week_start_date"]),
            models.Index(fields=["student_id", "week_offset"]),
        ]

    def __str__(self):
        return f"{self.student_id} @ {self.week_start_date} (offset={self.week_offset})"


class StudyPlanItem(models.Model):
    """
    
    projection
      - external_item_id  <- PlanItem.id ( "COMP9900-540003-1")
      - course_code       <- courseId
      - course_title      <- courseTitle
      - scheduled_date    <- date (YYYY-MM-DD)
      - minutes           <- minutes
      - part_index        <- partIndex
      - parts_count       <- partsCount
      - part_title        <- partTitle
      - color             <- color "#F6B48E"
      - completed         <- completed (bool)
    """
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name="items",
        db_index=True,
    )

  
    external_item_id = models.CharField(max_length=128)


    course_code = models.CharField(max_length=32, db_index=True)
    course_title = models.CharField(max_length=255, null=True, blank=True)


    scheduled_date = models.DateField(db_index=True)
    start_time = models.TimeField(null=True, blank=True)  
    minutes = models.IntegerField()

    part_index = models.IntegerField()
    parts_count = models.IntegerField()
    part_title = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=7, null=True, blank=True)  # e.g. "#F6B48E"

 
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)


    task_id = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_plan_item"
        unique_together = ("plan", "external_item_id")  
        indexes = [
            models.Index(fields=["plan", "scheduled_date"]),
            models.Index(fields=["course_code", "scheduled_date"]),
        ]

    def mark_completed(self):
      
        self.completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=["completed", "completed_at", "updated_at"])

    def __str__(self):
        return f"[{self.course_code}] {self.external_item_id} @ {self.scheduled_date}"
