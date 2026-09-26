from django.db import models

class Library(models.Model):
    book_id = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    issued_to = models.ForeignKey('student.Student', on_delete=models.SET_NULL, null=True, blank=True)
    issued_date = models.DateField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['issued_to', 'issued_date'], name='library_issued_to_date_idx'),
            models.Index(fields=['title'], name='library_title_idx'),
            models.Index(fields=['author'], name='library_author_idx'),
        ]

    def __str__(self):
        return f"{self.book_id} - {self.title}"
