"""
Sample Data Population Script
Run this to add sample students, marks, and attendance data
Usage: python manage.py shell < populate_sample_data.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_mis_project.settings')
django.setup()

from students.models import Student, Marks, Attendance

# Sample students data
sample_students = [
    {
        'name': 'John Doe',
        'reg_no': 'CSE001',
        'email': 'john.doe@example.com',
        'branch': 'CSE',
        'year': 3,
        'gender': 'M',
        'mobile': '9876543210',
        'password': 'student123'
    },
    {
        'name': 'Jane Smith',
        'reg_no': 'CSE002',
        'email': 'jane.smith@example.com',
        'branch': 'CSE',
        'year': 3,
        'gender': 'F',
        'mobile': '9876543211',
        'password': 'student123'
    },
    {
        'name': 'Alice Johnson',
        'reg_no': 'ECE001',
        'email': 'alice.johnson@example.com',
        'branch': 'ECE',
        'year': 2,
        'gender': 'F',
        'mobile': '9876543212',
        'password': 'student123'
    },
    {
        'name': 'Bob Williams',
        'reg_no': 'ME001',
        'email': 'bob.williams@example.com',
        'branch': 'ME',
        'year': 4,
        'gender': 'M',
        'mobile': '9876543213',
        'password': 'student123'
    },
    {
        'name': 'Emma Brown',
        'reg_no': 'EE001',
        'email': 'emma.brown@example.com',
        'branch': 'EE',
        'year': 1,
        'gender': 'F',
        'mobile': '9876543214',
        'password': 'student123'
    }
]

print("🚀 Starting to populate sample data...")
print("-" * 50)

# Create students
for student_data in sample_students:
    student, created = Student.objects.get_or_create(
        reg_no=student_data['reg_no'],
        defaults=student_data
    )
    
    if created:
        print(f"✅ Created student: {student.name} ({student.reg_no})")
        
        # Add sample marks
        marks = Marks.objects.create(
            student=student,
            subject1_name='Mathematics',
            subject1_ise1=18.0,
            subject1_mid=17.5,
            subject1_end=52.0,
            
            subject2_name='Physics',
            subject2_ise1=19.0,
            subject2_mid=18.0,
            subject2_end=55.0,
            
            subject3_name='Chemistry',
            subject3_ise1=17.0,
            subject3_mid=16.5,
            subject3_end=50.0,
            
            subject4_name='Programming',
            subject4_ise1=19.5,
            subject4_mid=19.0,
            subject4_end=58.0,
            
            subject5_name='Data Structures',
            subject5_ise1=18.5,
            subject5_mid=17.0,
            subject5_end=54.0
        )
        print(f"   📝 Added marks for {student.name}")
        
        # Add sample attendance
        attendance = Attendance.objects.create(
            student=student,
            total_classes=100,
            classes_attended=85
        )
        attendance.update_percentage()
        print(f"   📅 Added attendance for {student.name}: {attendance.attendance_percentage}%")
    else:
        print(f"⚠️  Student {student.name} already exists")

print("-" * 50)
print("✨ Sample data population completed!")
print(f"Total students in database: {Student.objects.count()}")
print("\n📚 You can now login with:")
print("   Admin - Username: admin, Password: admin123")
print("   Student - Reg No: CSE001, Password: student123")
