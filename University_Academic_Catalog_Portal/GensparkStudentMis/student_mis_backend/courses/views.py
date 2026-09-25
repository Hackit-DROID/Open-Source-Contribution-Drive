from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Instructor, CourseOffering, Enrollment
from .serializers import (
    CourseSerializer, InstructorSerializer,
    CourseOfferingSerializer, EnrollmentSerializer
)

class CourseViewSet(viewsets.ModelViewSet):
    """API endpoint for courses"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department']
    search_fields = ['course_code', 'course_name']

class InstructorViewSet(viewsets.ModelViewSet):
    """API endpoint for instructors"""
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department']
    search_fields = ['instructor_id', 'first_name', 'last_name', 'email']

class CourseOfferingViewSet(viewsets.ModelViewSet):
    """API endpoint for course offerings"""
    queryset = CourseOffering.objects.all()
    serializer_class = CourseOfferingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['course', 'instructor', 'semester', 'year', 'is_active']
    search_fields = ['course__course_code', 'course__course_name']
    
    @action(detail=True, methods=['get'])
    def enrolled_students(self, request, pk=None):
        """Get all students enrolled in this course offering"""
        offering = self.get_object()
        enrollments = offering.enrollments.filter(status='enrolled')
        return Response(EnrollmentSerializer(enrollments, many=True).data)

class EnrollmentViewSet(viewsets.ModelViewSet):
    """API endpoint for enrollments"""
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['student', 'course_offering', 'status']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    
    @action(detail=False, methods=['post'])
    def bulk_enroll(self, request):
        """Enroll multiple students in a course offering"""
        student_ids = request.data.get('student_ids', [])
        course_offering_id = request.data.get('course_offering_id')
        
        if not student_ids or not course_offering_id:
            return Response(
                {'error': 'student_ids and course_offering_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrolled = []
        errors = []
        
        for student_id in student_ids:
            try:
                enrollment = Enrollment.objects.create(
                    student_id=student_id,
                    course_offering_id=course_offering_id,
                    status='enrolled'
                )
                enrolled.append(enrollment.id)
            except Exception as e:
                errors.append({'student_id': student_id, 'error': str(e)})
        
        return Response({
            'enrolled': enrolled,
            'errors': errors
        })
