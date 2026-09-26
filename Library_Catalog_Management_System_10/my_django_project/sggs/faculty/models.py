from django.db import models

class Faculty(models.Model):
    emp_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, null=True, blank=True)   # nullable
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['department'], name='faculty_department_idx'),
        ]

    def __str__(self):
        return f"{self.emp_id} - {self.name}"
