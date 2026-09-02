from django.db import models
from students.models import Department, Student

class Course(models.Model):
    """Course model"""
    
    SEMESTER_CHOICES = [
        ('fall', 'Fall'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
    ]
    
    course_code = models.CharField(max_length=20, unique=True, primary_key=True)
    course_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.IntegerField(default=3)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='courses')
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='prerequisite_for')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course_code']
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

class Instructor(models.Model):
    """Instructor/Faculty model"""
    
    instructor_id = models.CharField(max_length=20, unique=True, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='instructors')
    office_location = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class CourseOffering(models.Model):
    """Course offering for a specific semester/year"""
    
    SEMESTER_CHOICES = [
        ('fall', 'Fall'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    instructor = models.ForeignKey(Instructor, on_delete=models.PROTECT, related_name='course_offerings')
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    year = models.IntegerField()
    
    # Schedule
    schedule = models.TextField(help_text="e.g., Mon/Wed/Fri 10:00-11:00")
    room = models.CharField(max_length=50, blank=True)
    
    # Capacity
    max_capacity = models.IntegerField(default=30)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-semester']
        unique_together = ['course', 'semester', 'year']
    
    def __str__(self):
        return f"{self.course.course_code} - {self.semester} {self.year}"
    
    @property
    def enrollment_count(self):
        return self.enrollments.filter(status='enrolled').count()
    
    @property
    def available_seats(self):
        return self.max_capacity - self.enrollment_count

class Enrollment(models.Model):
    """Student enrollment in course offerings"""
    
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    
    # Final grade (populated at end of semester)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['student', 'course_offering']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course_offering}"
    
    def calculate_letter_grade(self):
        """Calculate letter grade from final grade"""
        if self.final_grade is None:
            return ''
        
        grade = float(self.final_grade)
        if grade >= 90:
            return 'A'
        elif grade >= 80:
            return 'B'
        elif grade >= 70:
            return 'C'
        elif grade >= 60:
            return 'D'
        else:
            return 'F'
