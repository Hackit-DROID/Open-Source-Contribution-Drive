from rest_framework import serializers
from .models import AttendanceRecord, AttendanceSummary

class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course_offering.course.course_name', read_only=True)
    course_code = serializers.CharField(source='course_offering.course.course_code', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AttendanceSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    course_name = serializers.CharField(source='course_offering.course.course_name', read_only=True)
    course_code = serializers.CharField(source='course_offering.course.course_code', read_only=True)
    
    class Meta:
        model = AttendanceSummary
        fields = '__all__'
        read_only_fields = ['updated_at']
