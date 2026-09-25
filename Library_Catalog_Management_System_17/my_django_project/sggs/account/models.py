from django.db import models

class Account(models.Model):   # ✅ Capitalized
    regno = models.CharField(max_length=20, unique=True)
    fees_type = models.CharField(max_length=100)
    amount = models.IntegerField()
    
    def __str__(self):
        return f"{self.regno} - {self.fees_type}"
