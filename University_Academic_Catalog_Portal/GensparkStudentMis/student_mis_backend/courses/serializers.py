from rest_framework import serializers
from .models import Course, Instructor, CourseOffering, Enrollment

class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'

class InstructorSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Instructor
        fields = '__all__'

class CourseOfferingSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CourseOffering
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course_offering.course.course_name', read_only=True)
    course_code = serializers.CharField(source='course_offering.course.course_code', read_only=True)
    semester = serializers.CharField(source='course_offering.semester', read_only=True)
    year = serializers.IntegerField(source='course_offering.year', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['enrollment_date', 'created_at', 'updated_at']
