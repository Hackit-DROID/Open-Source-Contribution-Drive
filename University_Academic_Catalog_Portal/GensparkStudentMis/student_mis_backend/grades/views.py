from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from .models import AssessmentType, Assessment, Grade, GradeReport
from .serializers import (
    AssessmentTypeSerializer, AssessmentSerializer,
    GradeSerializer, GradeReportSerializer
)

class AssessmentTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for assessment types"""
    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer

class AssessmentViewSet(viewsets.ModelViewSet):
    """API endpoint for assessments"""
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course_offering', 'assessment_type', 'is_published']
    search_fields = ['title']
    ordering_fields = ['due_date', 'assigned_date']
    ordering = ['-due_date']

class GradeViewSet(viewsets.ModelViewSet):
    """API endpoint for grades"""
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'assessment', 'enrollment']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    ordering_fields = ['graded_date', 'score']
    ordering = ['-graded_date']
    
    @action(detail=False, methods=['post'])
    def bulk_grade(self, request):
        """Grade multiple students for an assessment"""
        assessment_id = request.data.get('assessment_id')
        grades_data = request.data.get('grades', [])
        
        if not assessment_id or not grades_data:
            return Response(
                {'error': 'assessment_id and grades data required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        graded = []
        errors = []
        
        for grade_data in grades_data:
            try:
                grade, created = Grade.objects.update_or_create(
                    student_id=grade_data['student_id'],
                    assessment_id=assessment_id,
                    enrollment_id=grade_data['enrollment_id'],
                    defaults={
                        'score': grade_data['score'],
                        'feedback': grade_data.get('feedback', ''),
                        'graded_by': request.data.get('graded_by', ''),
                        'is_late': grade_data.get('is_late', False),
                        'late_penalty': grade_data.get('late_penalty', 0)
                    }
                )
                graded.append(grade.id)
            except Exception as e:
                errors.append({'student_id': grade_data.get('student_id'), 'error': str(e)})
        
        return Response({
            'graded': len(graded),
            'errors': errors
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get grade statistics for an assessment"""
        assessment_id = request.query_params.get('assessment_id')
        
        if not assessment_id:
            return Response(
                {'error': 'assessment_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        grades = Grade.objects.filter(assessment_id=assessment_id)
        
        stats = grades.aggregate(
            count=Count('id'),
            average_score=Avg('score'),
            average_percentage=Avg('percentage')
        )
        
        # Grade distribution
        grade_distribution = {
            'A': grades.filter(percentage__gte=90).count(),
            'B': grades.filter(percentage__gte=80, percentage__lt=90).count(),
            'C': grades.filter(percentage__gte=70, percentage__lt=80).count(),
            'D': grades.filter(percentage__gte=60, percentage__lt=70).count(),
            'F': grades.filter(percentage__lt=60).count(),
        }
        
        stats['grade_distribution'] = grade_distribution
        
        return Response(stats)

class GradeReportViewSet(viewsets.ModelViewSet):
    """API endpoint for grade reports"""
    queryset = GradeReport.objects.all()
    serializer_class = GradeReportSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'enrollment', 'is_finalized', 'letter_grade']
    ordering_fields = ['percentage', 'gpa']
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calculate final grade for a report"""
        report = self.get_object()
        report.calculate_final_grade()
        return Response(GradeReportSerializer(report).data)
    
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """Finalize a grade report"""
        report = self.get_object()
        report.calculate_final_grade()
        report.is_finalized = True
        from datetime.date import today
        report.finalized_date = today()
        report.save()
        
        # Also update enrollment final grade
        report.enrollment.final_grade = report.percentage
        report.enrollment.letter_grade = report.letter_grade
        report.enrollment.save()
        
        return Response(GradeReportSerializer(report).data)
