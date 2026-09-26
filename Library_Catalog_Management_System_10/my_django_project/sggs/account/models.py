from django.db import models
from student.models import Student
from library.models import Library

class Account(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.SET_NULL, null=True, blank=True)
    fees_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    due = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    branch = models.CharField(max_length=50, default='Unknown')  # optional if you want branch here

    class Meta:
        indexes = [
            models.Index(fields=['student', 'library'], name='account_student_library_idx'),
            models.Index(fields=['due'], name='account_due_idx'),
        ]

    def __str__(self):
        return f"{self.student.name} Account"
