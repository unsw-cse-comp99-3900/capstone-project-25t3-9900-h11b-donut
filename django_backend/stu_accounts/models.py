from django.db import models
from decimal import Decimal

class StudentAccount(models.Model):
    student_id = models.CharField(max_length=32, primary_key=True)
    email = models.CharField(max_length=254, unique=True)
    password_hash = models.CharField(max_length=60)
    avatar_url = models.CharField(max_length=512, null=True, blank=True)
    name = models.CharField(max_length=100,default='Unknown',null=False, blank=False)
    current_token = models.CharField(
        max_length=128, null=True, blank=True, db_index=True
    )
    bonus = models.DecimalField(
        max_digits=5,     
        decimal_places=2, 
        default=Decimal("0.00"),
    )
    token_issued_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "accounts_studentaccount"