from django.db import models
from django.utils import timezone


class StudyPlan(models.Model):
    """
    一名学生的一周计划（头表/批次表）
    唯一性：student_id + week_start_date（周一）唯一
    """
    id = models.BigAutoField(primary_key=True)
    student_id = models.CharField(max_length=64, db_index=True)
    week_start_date = models.DateField()  # 建议存该周周一
    week_offset = models.IntegerField(default=0)
    tz = models.CharField(max_length=64, default='Australia/Sydney')

    SOURCE_CHOICES = (
        ('ai', 'AI'),
        ('manual', 'Manual'),
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='ai')

    # 预留：偏好/生成参数等
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
    一周计划中的明细条目（与你的 PlanItem 对齐）
    字段映射：
      - external_item_id  <- PlanItem.id (如 "COMP9900-540003-1")
      - course_code       <- courseId
      - course_title      <- courseTitle（冗余展示）
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

    # —— 业务主键（用于幂等/覆盖写入）——
    external_item_id = models.CharField(max_length=128)

    # —— 课程关联（弱关联，便于直出）——
    course_code = models.CharField(max_length=32, db_index=True)
    course_title = models.CharField(max_length=255, null=True, blank=True)

    # —— 安排信息 —— 
    scheduled_date = models.DateField(db_index=True)
    start_time = models.TimeField(null=True, blank=True)  # 现在可不填，后续日历拖拽可用
    minutes = models.IntegerField()

    part_index = models.IntegerField()
    parts_count = models.IntegerField()
    part_title = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=7, null=True, blank=True)  # e.g. "#F6B48E"

    # —— 状态 —— 
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # —— 预留：若将来需要挂到后端任务ID —— 
    task_id = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_plan_item"
        unique_together = ("plan", "external_item_id")  # 防重复插入同一周的同一条
        indexes = [
            models.Index(fields=["plan", "scheduled_date"]),
            models.Index(fields=["course_code", "scheduled_date"]),
        ]

    def mark_completed(self):
        """简便方法：在视图里调用以勾选完成。"""
        self.completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=["completed", "completed_at", "updated_at"])

    def __str__(self):
        return f"[{self.course_code}] {self.external_item_id} @ {self.scheduled_date}"
