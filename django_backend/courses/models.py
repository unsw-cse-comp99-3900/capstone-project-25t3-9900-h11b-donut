from django.db import models
from accounts.models import StudentAccount

class Course(models.Model):
    course_code = models.CharField(max_length=16, primary_key=True)
    course_name = models.CharField(max_length=255)

    class Meta:
        db_table = "courses"

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class StudentCourse(models.Model):
    student = models.ForeignKey(StudentAccount, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        db_table = "student_courses"
        unique_together = ("student", "course")


class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=1024)

    class Meta:
        db_table = "materials"

    def __str__(self):
        return self.title
