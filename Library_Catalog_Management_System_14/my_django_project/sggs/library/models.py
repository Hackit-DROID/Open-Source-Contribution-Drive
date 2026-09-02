

# Create your models here.
from django.db import models

class Library(models.Model):
    regno = models.CharField(max_length=20)   # Student's registration number
    book_name = models.CharField(max_length=200)
    date_issue = models.DateField()
    date_return = models.DateField(null=True, blank=True)  # return date may be empty

    def __str__(self):
        return f"{self.regno} - {self.book_name}"
