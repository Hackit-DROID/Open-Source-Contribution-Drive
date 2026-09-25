from django.db import models
from students.models import Student
from courses.models import CourseOffering

class AttendanceRecord(models.Model):
    """Attendance tracking for students in course offerings"""
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Additional details
    remarks = models.TextField(blank=True)
    marked_by = models.CharField(max_length=100, blank=True)  # Who marked the attendance
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'course_offering', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['student', 'course_offering']),
        ]
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course_offering} - {self.date} - {self.status}"

class AttendanceSummary(models.Model):
    """Summary of attendance for a student in a course"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_summaries')
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='attendance_summaries')
    
    total_classes = models.IntegerField(default=0)
    classes_present = models.IntegerField(default=0)
    classes_absent = models.IntegerField(default=0)
    classes_late = models.IntegerField(default=0)
    classes_excused = models.IntegerField(default=0)
    
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course_offering']
        verbose_name_plural = 'Attendance summaries'
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course_offering} - {self.attendance_percentage}%"
    
    def update_summary(self):
        """Update attendance summary based on records"""
        records = AttendanceRecord.objects.filter(
            student=self.student,
            course_offering=self.course_offering
        )
        
        self.total_classes = records.count()
        self.classes_present = records.filter(status='present').count()
        self.classes_absent = records.filter(status='absent').count()
        self.classes_late = records.filter(status='late').count()
        self.classes_excused = records.filter(status='excused').count()
        
        if self.total_classes > 0:
            self.attendance_percentage = (self.classes_present / self.total_classes) * 100
        else:
            self.attendance_percentage = 0
        
        self.save()
