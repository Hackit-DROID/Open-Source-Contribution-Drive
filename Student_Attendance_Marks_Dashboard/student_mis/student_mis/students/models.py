from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Student(models.Model):
    """Student Information Model"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science Engineering'),
        ('ECE', 'Electronics and Communication Engineering'),
        ('ME', 'Mechanical Engineering'),
        ('EE', 'Electrical Engineering'),
        ('CE', 'Civil Engineering'),
    ]
    
    YEAR_CHOICES = [
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year'),
    ]
    
    name = models.CharField(max_length=200)
    reg_no = models.CharField(max_length=50, unique=True, primary_key=True)
    email = models.EmailField(unique=True)
    branch = models.CharField(max_length=10, choices=BRANCH_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    mobile = models.CharField(max_length=15)
    password = models.CharField(max_length=128, default='student123')  # Default password
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.reg_no})"
    
    class Meta:
        ordering = ['name']


class Marks(models.Model):
    """Student Marks Model - Stores marks for 5 subjects"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True, related_name='marks')
    
    # Subject 1
    subject1_name = models.CharField(max_length=100, default='Mathematics')
    subject1_ise1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject1_mid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject1_end = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Subject 2
    subject2_name = models.CharField(max_length=100, default='Physics')
    subject2_ise1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject2_mid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject2_end = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Subject 3
    subject3_name = models.CharField(max_length=100, default='Chemistry')
    subject3_ise1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject3_mid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject3_end = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Subject 4
    subject4_name = models.CharField(max_length=100, default='Programming')
    subject4_ise1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject4_mid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject4_end = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Subject 5
    subject5_name = models.CharField(max_length=100, default='Data Structures')
    subject5_ise1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject5_mid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subject5_end = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_subject_total(self, subject_num):
        """Calculate total marks for a subject with weightage: ISE1(20%), Mid(20%), End(60%)"""
        ise1 = getattr(self, f'subject{subject_num}_ise1')
        mid = getattr(self, f'subject{subject_num}_mid')
        end = getattr(self, f'subject{subject_num}_end')
        return (ise1 * Decimal('0.2')) + (mid * Decimal('0.2')) + (end * Decimal('0.6'))
    
    def get_all_totals(self):
        """Get total marks for all subjects"""
        return {
            'subject1': self.calculate_subject_total(1),
            'subject2': self.calculate_subject_total(2),
            'subject3': self.calculate_subject_total(3),
            'subject4': self.calculate_subject_total(4),
            'subject5': self.calculate_subject_total(5),
        }
    
    def get_overall_percentage(self):
        """Calculate overall percentage"""
        totals = self.get_all_totals()
        total_marks = sum(totals.values())
        return (total_marks / Decimal('500')) * Decimal('100')  # Assuming each subject is out of 100
    
    def __str__(self):
        return f"Marks for {self.student.name}"


class Attendance(models.Model):
    """Student Attendance Model"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True, related_name='attendance')
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_classes = models.IntegerField(default=0)
    classes_attended = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_percentage(self):
        """Calculate attendance percentage"""
        if self.total_classes > 0:
            self.attendance_percentage = (Decimal(self.classes_attended) / Decimal(self.total_classes)) * Decimal('100')
        else:
            self.attendance_percentage = Decimal('0')
        self.save()
    
    def __str__(self):
        return f"Attendance for {self.student.name}: {self.attendance_percentage}%"
