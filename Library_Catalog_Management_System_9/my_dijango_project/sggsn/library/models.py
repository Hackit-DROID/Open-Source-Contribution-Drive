from django.utils import timezone

from django.db import models


class Library(models.Model):
    student = models.CharField(max_length=100)
    regno = models.CharField(max_length=20)
    book_title = models.CharField(max_length=200)
    issue_date = models.DateField()
    return_date = models.DateField(default=timezone.now)   # ❌ this causes the problem
    fine = models.DecimalField(max_digits=6, decimal_places=2)
