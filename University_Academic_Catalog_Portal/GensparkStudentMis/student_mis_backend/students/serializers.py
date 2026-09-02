from rest_framework import serializers
from .models import Department, Student

class DepartmentSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = '__all__'
    
    def get_student_count(self, obj):
        return obj.students.filter(status='active').count()

class StudentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class StudentListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'department', 'department_name',
            'year', 'status', 'enrollment_date'
        ]
