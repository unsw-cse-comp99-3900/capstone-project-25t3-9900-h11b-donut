from django.db import models

# 课程目录：用于搜索/展示
class CourseCatalog(models.Model):
    code = models.CharField(max_length=16, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    illustration = models.CharField(max_length=32, default="orange")  # 前端期望的插图标识：orange|student|admin

    class Meta:
        db_table = "course_catalog"

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


# 课程任务：课程内的发布任务
class CourseTask(models.Model):
    id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=16)  # 直接存课程代码，Sprint1 简化
    title = models.CharField(max_length=255)
    deadline = models.DateField()
    brief = models.TextField(blank=True)
    percent_contribution = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "course_task"

    def __str__(self) -> str:
        return f"{self.course_code} - {self.title}"


# 学生选课
class StudentEnrollment(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    course_code = models.CharField(max_length=16)

    class Meta:
        db_table = "student_enrollment"
        unique_together = ("student_id", "course_code")


# 任务进度（按学生-任务）
class TaskProgress(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=64)
    task_id = models.PositiveIntegerField()
    progress = models.PositiveIntegerField(default=0)  # 0..100

    class Meta:
        db_table = "task_progress"
        unique_together = ("student_id", "task_id")


# 学习材料（保持不变：与课程关联并提供下载）
class Material(models.Model):
    course_code = models.CharField(max_length=16)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=1024)  # 可为后端下载路径或外链

    class Meta:
        db_table = "material"

    def __str__(self) -> str:
        return f"{self.title}"