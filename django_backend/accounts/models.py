from django.db import models


class StudentAccount(models.Model):
    student_id = models.CharField(max_length=32, primary_key=True)
    email = models.CharField(max_length=254, unique=True)
    password_hash = models.CharField(max_length=60)
    avatar_url = models.CharField(max_length=512, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)