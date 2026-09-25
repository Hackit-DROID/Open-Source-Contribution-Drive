# students/models.py

from django.db import models

class Student(models.Model):
    # Defining choices for year and branch for better data consistency
    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
    ]
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science'),
        ('IT', 'Information Technology'),
        ('ENTC', 'Electronics & Telecommunication'),
        ('MECH', 'Mechanical'),
        ('CIVIL', 'Civil'),
    ]

    name = models.CharField(max_length=100)
    registration_no = models.CharField(max_length=20, unique=True, verbose_name="Registration Number")
    year = models.CharField(max_length=1, choices=YEAR_CHOICES)
    branch = models.CharField(max_length=5, choices=BRANCH_CHOICES)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True, verbose_name="Phone Number")

    def __str__(self):
        return f"{self.name} ({self.registration_no})"