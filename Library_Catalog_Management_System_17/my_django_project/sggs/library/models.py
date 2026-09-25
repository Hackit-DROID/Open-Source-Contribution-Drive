from django.db import models

class Library(models.Model):
    regno = models.CharField(max_length=20, unique=True)   # Registration number
    book_name = models.CharField(max_length=200)
    date_issue = models.DateField()
    date_return = models.DateField()

    def __str__(self):
        return f"{self.regno} - {self.book_name}"
