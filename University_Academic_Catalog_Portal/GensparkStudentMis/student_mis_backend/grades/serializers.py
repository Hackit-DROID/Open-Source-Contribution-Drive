from rest_framework import serializers
from .models import AssessmentType, Assessment, Grade, GradeReport

class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = '__all__'

class AssessmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course_offering.course.course_name', read_only=True)
    course_code = serializers.CharField(source='course_offering.course.course_code', read_only=True)
    assessment_type_name = serializers.CharField(source='assessment_type.name', read_only=True)
    
    class Meta:
        model = Assessment
        fields = '__all__'

class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    max_score = serializers.DecimalField(source='assessment.max_score', max_digits=6, decimal_places=2, read_only=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    weighted_score = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    
    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ['graded_date', 'created_at', 'updated_at']

class GradeReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    course_name = serializers.CharField(source='enrollment.course_offering.course.course_name', read_only=True)
    course_code = serializers.CharField(source='enrollment.course_offering.course.course_code', read_only=True)
    
    class Meta:
        model = GradeReport
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
