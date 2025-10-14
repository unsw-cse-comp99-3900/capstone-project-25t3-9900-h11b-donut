from django.db import models

class WeeklyPlan(models.Model):
    """
    每周计划（按学生ID与周偏移存储）
    Sprint1 原型可选：保留与内存存储一致的结构，后续迁移时直接落库
    """
    student_id = models.CharField(max_length=32)
    week_offset = models.IntegerField()
    # 简化存储：JSON 化的计划项列表（与前端 ApiPlanItem 对齐）
    items_json = models.JSONField(default=list)

    class Meta:
        db_table = "weekly_plans"
        unique_together = ("student_id", "week_offset")

    def __str__(self):
        return f"Plan<{self.student_id}>@{self.week_offset}"