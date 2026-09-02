from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Department, Student
from .serializers import DepartmentSerializer, StudentSerializer, StudentListSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for departments
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']

class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for students
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'year', 'status', 'gender']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']
    ordering_fields = ['student_id', 'last_name', 'enrollment_date']
    ordering = ['student_id']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics"""
        total = Student.objects.count()
        active = Student.objects.filter(status='active').count()
        by_year = {}
        for year in [1, 2, 3, 4]:
            by_year[f'year_{year}'] = Student.objects.filter(year=year, status='active').count()
        
        by_department = {}
        for dept in Department.objects.all():
            by_department[dept.name] = dept.students.filter(status='active').count()
        
        return Response({
            'total_students': total,
            'active_students': active,
            'students_by_year': by_year,
            'students_by_department': by_department,
        })
    
    @action(detail=True, methods=['get'])
    def academic_record(self, request, pk=None):
        """Get complete academic record for a student"""
        student = self.get_object()
        from courses.serializers import EnrollmentSerializer
        from grades.serializers import GradeReportSerializer
        
        enrollments = student.enrollments.all()
        grade_reports = student.grade_reports.all()
        
        return Response({
            'student': StudentSerializer(student).data,
            'enrollments': EnrollmentSerializer(enrollments, many=True).data,
            'grade_reports': GradeReportSerializer(grade_reports, many=True).data,
        })
