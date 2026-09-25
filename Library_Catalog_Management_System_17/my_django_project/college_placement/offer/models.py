from django.db import models
from student.models import Student
from company.models import Company

class Offer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    package = models.DecimalField(max_digits=10, decimal_places=2)
    offer_date = models.DateField()

    def __str__(self):
        return f"Offer: {self.student.name} - {self.company.name} ({self.role})"
