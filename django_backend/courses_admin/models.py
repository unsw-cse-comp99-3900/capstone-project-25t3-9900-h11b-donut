from django.db import models
from courses.models import CourseCatalog       
from adm_accounts.models import AdminAccount   

class CourseAdmin(models.Model):
    # fk-> CourseCatalog code
    code = models.OneToOneField(
        CourseCatalog,
        on_delete=models.CASCADE,
        to_field='code',
        db_column='code',
        primary_key=True  
    )

    # fk ->  AdminAccount admin_id
    admin = models.ForeignKey(
        AdminAccount,
        on_delete=models.CASCADE,
        to_field='admin_id',
        db_column='admin_id',
        related_name='created_courses'
    )

=
    class Meta:
        db_table = 'course_admin'   
        verbose_name = 'Course-Admin Mapping'
        verbose_name_plural = 'Course-Admin Mappings'

    def __str__(self):
        return f"{self.code.code} - {self.admin.admin_id}"
