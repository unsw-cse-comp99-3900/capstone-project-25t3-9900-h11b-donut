from django.db import models
from courses.models import CourseCatalog        # 引用课程目录
from adm_accounts.models import AdminAccount    # 引用管理员表

class CourseAdmin(models.Model):
    # 外键：对应 CourseCatalog 的主键 code
    code = models.OneToOneField(
        CourseCatalog,
        on_delete=models.CASCADE,
        to_field='code',
        db_column='code',
        primary_key=True  # 让 code 作为主键
    )

    # 外键：对应 AdminAccount 的主键 admin_id
    admin = models.ForeignKey(
        AdminAccount,
        on_delete=models.CASCADE,
        to_field='admin_id',
        db_column='admin_id',
        related_name='created_courses'
    )

    # 可选：记录创建时间
    class Meta:
        db_table = 'course_admin'   # 数据库中的表名
        verbose_name = 'Course-Admin Mapping'
        verbose_name_plural = 'Course-Admin Mappings'

    def __str__(self):
        return f"{self.code.code} - {self.admin.admin_id}"
