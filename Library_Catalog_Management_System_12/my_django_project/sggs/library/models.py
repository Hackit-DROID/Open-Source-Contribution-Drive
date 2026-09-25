from django.db import models

class Library(models.Model):
    book_id = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    issued_to = models.ForeignKey('student.Student', on_delete=models.SET_NULL, null=True, blank=True)
    issued_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.book_id} - {self.title}"
