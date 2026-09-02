from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import AttendanceRecord, AttendanceSummary
from .serializers import AttendanceRecordSerializer, AttendanceSummarySerializer

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """API endpoint for attendance records"""
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'course_offering', 'date', 'status']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    ordering_fields = ['date']
    ordering = ['-date']
    
    @action(detail=False, methods=['post'])
    def mark_bulk_attendance(self, request):
        """Mark attendance for multiple students at once"""
        course_offering_id = request.data.get('course_offering_id')
        date = request.data.get('date')
        attendance_data = request.data.get('attendance', [])
        
        if not all([course_offering_id, date, attendance_data]):
            return Response(
                {'error': 'course_offering_id, date, and attendance data required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        marked = []
        errors = []
        
        for record in attendance_data:
            try:
                attendance, created = AttendanceRecord.objects.update_or_create(
                    student_id=record['student_id'],
                    course_offering_id=course_offering_id,
                    date=date,
                    defaults={
                        'status': record['status'],
                        'remarks': record.get('remarks', ''),
                        'marked_by': request.data.get('marked_by', '')
                    }
                )
                marked.append(attendance.id)
                
                # Update summary
                summary, _ = AttendanceSummary.objects.get_or_create(
                    student_id=record['student_id'],
                    course_offering_id=course_offering_id
                )
                summary.update_summary()
                
            except Exception as e:
                errors.append({'student_id': record.get('student_id'), 'error': str(e)})
        
        return Response({
            'marked': len(marked),
            'errors': errors
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get attendance statistics"""
        course_offering_id = request.query_params.get('course_offering_id')
        
        if not course_offering_id:
            return Response(
                {'error': 'course_offering_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        records = AttendanceRecord.objects.filter(course_offering_id=course_offering_id)
        
        stats = records.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
            excused=Count('id', filter=Q(status='excused'))
        )
        
        if stats['total'] > 0:
            stats['attendance_rate'] = (stats['present'] / stats['total']) * 100
        else:
            stats['attendance_rate'] = 0
        
        return Response(stats)

class AttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for attendance summaries (read-only)"""
    queryset = AttendanceSummary.objects.all()
    serializer_class = AttendanceSummarySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'course_offering']
    ordering_fields = ['attendance_percentage']
    
    @action(detail=False, methods=['post'])
    def update_all(self, request):
        """Update all attendance summaries"""
        course_offering_id = request.data.get('course_offering_id')
        
        if course_offering_id:
            summaries = AttendanceSummary.objects.filter(course_offering_id=course_offering_id)
        else:
            summaries = AttendanceSummary.objects.all()
        
        for summary in summaries:
            summary.update_summary()
        
        return Response({'updated': summaries.count()})
