from django.db import models
class AdminAccount(models.Model):
    
    admin_id = models.CharField(max_length=32, primary_key=True)
    email = models.CharField(max_length=254, unique=True)     
    full_name = models.CharField(max_length=100, default='Unknown', null=False, blank=False)
    password_hash = models.CharField(max_length=128)          
    avatar_url = models.CharField(max_length=512, null=True, blank=True)  


    current_token = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    token_issued_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = "accounts_adminaccount"  
        indexes = [ #accelerate the speed of searching
            models.Index(fields=["current_token"]),
        ]

    def __str__(self):
        return self.admin_id