from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from courses.models import CourseOffering, Enrollment

class AssessmentType(models.Model):
    """Types of assessments (Midterm, Final, Quiz, Assignment, etc.)"""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    weight_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight in final grade calculation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.weight_percentage}%)"

class Assessment(models.Model):
    """Specific assessment instance for a course offering"""
    
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='assessments')
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.PROTECT)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    weight_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Dates
    assigned_date = models.DateField()
    due_date = models.DateField()
    
    # Status
    is_published = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.course_offering} - {self.title}"

class Grade(models.Model):
    """Individual grade for a student on an assessment"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='grades')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Feedback
    feedback = models.TextField(blank=True)
    graded_by = models.CharField(max_length=100, blank=True)
    graded_date = models.DateField(auto_now_add=True)
    
    # Late submission
    is_late = models.BooleanField(default=False)
    late_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'assessment']
        ordering = ['-graded_date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.assessment.title} - {self.score}"
    
    @property
    def percentage(self):
        """Calculate percentage score"""
        if self.assessment.max_score > 0:
            return (float(self.score) / float(self.assessment.max_score)) * 100
        return 0
    
    @property
    def weighted_score(self):
        """Calculate weighted score for final grade"""
        return (self.percentage / 100) * float(self.assessment.weight_percentage)

class GradeReport(models.Model):
    """Comprehensive grade report for a student in a course"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grade_reports')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grade_reports')
    
    # Calculated grades
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    letter_grade = models.CharField(max_length=2, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Status
    is_finalized = models.BooleanField(default=False)
    finalized_date = models.DateField(null=True, blank=True)
    
    # Comments
    instructor_comments = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'enrollment']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.enrollment.course_offering} - {self.letter_grade}"
    
    def calculate_final_grade(self):
        """Calculate final grade based on all assessments"""
        grades = Grade.objects.filter(
            student=self.student,
            enrollment=self.enrollment
        )
        
        total_weighted = sum(grade.weighted_score for grade in grades)
        self.total_score = total_weighted
        self.percentage = total_weighted
        self.letter_grade = self.calculate_letter_grade()
        self.gpa = self.calculate_gpa()
        self.save()
    
    def calculate_letter_grade(self):
        """Convert percentage to letter grade"""
        percentage = float(self.percentage)
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def calculate_gpa(self):
        """Convert letter grade to GPA"""
        grade_to_gpa = {
            'A': 4.0,
            'B': 3.0,
            'C': 2.0,
            'D': 1.0,
            'F': 0.0,
        }
        return grade_to_gpa.get(self.letter_grade, 0.0)
