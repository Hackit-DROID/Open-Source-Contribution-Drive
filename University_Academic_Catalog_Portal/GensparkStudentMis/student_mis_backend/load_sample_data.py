#!/usr/bin/env python
"""Load sample data into the database"""
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_mis_backend.settings')
django.setup()

from students.models import Department, Student
from courses.models import Course, Instructor, CourseOffering, Enrollment

def load_data():
    print("Loading sample data...")
    
    # Create Departments
    print("Creating departments...")
    cs_dept, _ = Department.objects.get_or_create(
        code='CS',
        defaults={'name': 'Computer Science', 'description': 'Computer Science and Technology'}
    )
    eng_dept, _ = Department.objects.get_or_create(
        code='ENG',
        defaults={'name': 'Engineering', 'description': 'General Engineering'}
    )
    bus_dept, _ = Department.objects.get_or_create(
        code='BUS',
        defaults={'name': 'Business', 'description': 'Business Administration'}
    )
    arts_dept, _ = Department.objects.get_or_create(
        code='ART',
        defaults={'name': 'Arts', 'description': 'Liberal Arts'}
    )
    
    # Create Students
    print("Creating students...")
    students_data = [
        {
            'student_id': 'STU001',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@university.edu',
            'phone': '+15550101',
            'department': cs_dept,
            'year': 2,
            'date_of_birth': date(2002, 5, 15),
            'gender': 'M',
            'address': '123 Main St',
            'city': 'Boston',
            'state': 'MA',
            'country': 'USA',
            'postal_code': '02101',
            'enrollment_date': date(2022, 9, 1)
        },
        {
            'student_id': 'STU002',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@university.edu',
            'phone': '+15550102',
            'department': eng_dept,
            'year': 3,
            'date_of_birth': date(2001, 8, 22),
            'gender': 'F',
            'address': '456 Oak Ave',
            'city': 'Boston',
            'state': 'MA',
            'country': 'USA',
            'postal_code': '02102',
            'enrollment_date': date(2021, 9, 1)
        },
        {
            'student_id': 'STU003',
            'first_name': 'Mike',
            'last_name': 'Johnson',
            'email': 'mike.johnson@university.edu',
            'phone': '+15550103',
            'department': bus_dept,
            'year': 1,
            'date_of_birth': date(2003, 2, 10),
            'gender': 'M',
            'address': '789 Pine Rd',
            'city': 'Boston',
            'state': 'MA',
            'country': 'USA',
            'postal_code': '02103',
            'enrollment_date': date(2023, 9, 1)
        },
        {
            'student_id': 'STU004',
            'first_name': 'Emily',
            'last_name': 'Brown',
            'email': 'emily.brown@university.edu',
            'phone': '+15550104',
            'department': cs_dept,
            'year': 4,
            'date_of_birth': date(2000, 11, 30),
            'gender': 'F',
            'address': '321 Elm St',
            'city': 'Boston',
            'state': 'MA',
            'country': 'USA',
            'postal_code': '02104',
            'enrollment_date': date(2020, 9, 1)
        },
        {
            'student_id': 'STU005',
            'first_name': 'David',
            'last_name': 'Wilson',
            'email': 'david.wilson@university.edu',
            'phone': '+15550105',
            'department': arts_dept,
            'year': 2,
            'date_of_birth': date(2002, 7, 18),
            'gender': 'M',
            'address': '654 Maple Dr',
            'city': 'Boston',
            'state': 'MA',
            'country': 'USA',
            'postal_code': '02105',
            'enrollment_date': date(2022, 9, 1)
        }
    ]
    
    for student_data in students_data:
        student, created = Student.objects.get_or_create(
            student_id=student_data['student_id'],
            defaults=student_data
        )
        if created:
            print(f"  Created student: {student.student_id}")
    
    # Create Instructors
    print("Creating instructors...")
    turing, _ = Instructor.objects.get_or_create(
        instructor_id='INS001',
        defaults={
            'first_name': 'Alan',
            'last_name': 'Turing',
            'email': 'a.turing@university.edu',
            'phone': '+15551001',
            'department': cs_dept,
            'office_location': 'CS Building, Room 301'
        }
    )
    
    hopper, _ = Instructor.objects.get_or_create(
        instructor_id='INS002',
        defaults={
            'first_name': 'Grace',
            'last_name': 'Hopper',
            'email': 'g.hopper@university.edu',
            'phone': '+15551002',
            'department': cs_dept,
            'office_location': 'CS Building, Room 305'
        }
    )
    
    # Create Courses
    print("Creating courses...")
    courses_data = [
        {
            'course_code': 'CS101',
            'course_name': 'Introduction to Programming',
            'description': 'Basic programming concepts and problem solving',
            'credits': 3,
            'department': cs_dept
        },
        {
            'course_code': 'CS201',
            'course_name': 'Data Structures',
            'description': 'Advanced data structures and algorithms',
            'credits': 4,
            'department': cs_dept
        },
        {
            'course_code': 'ENG101',
            'course_name': 'Engineering Mathematics',
            'description': 'Mathematical foundations for engineering',
            'credits': 4,
            'department': eng_dept
        },
        {
            'course_code': 'BUS101',
            'course_name': 'Business Administration',
            'description': 'Fundamentals of business management',
            'credits': 3,
            'department': bus_dept
        }
    ]
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            course_code=course_data['course_code'],
            defaults=course_data
        )
        if created:
            print(f"  Created course: {course.course_code}")
    
    # Create Course Offerings for Fall 2024
    print("Creating course offerings...")
    cs101_offering, _ = CourseOffering.objects.get_or_create(
        course=Course.objects.get(course_code='CS101'),
        semester='fall',
        year=2024,
        defaults={
            'instructor': turing,
            'schedule': 'Mon/Wed/Fri 10:00-11:00',
            'room': 'CS-101',
            'max_capacity': 30
        }
    )
    
    cs201_offering, _ = CourseOffering.objects.get_or_create(
        course=Course.objects.get(course_code='CS201'),
        semester='fall',
        year=2024,
        defaults={
            'instructor': hopper,
            'schedule': 'Tue/Thu 14:00-15:30',
            'room': 'CS-201',
            'max_capacity': 25
        }
    )
    
    print("\n✅ Sample data loaded successfully!")
    print(f"\nCreated:")
    print(f"  - {Department.objects.count()} departments")
    print(f"  - {Student.objects.count()} students")
    print(f"  - {Instructor.objects.count()} instructors")
    print(f"  - {Course.objects.count()} courses")
    print(f"  - {CourseOffering.objects.count()} course offerings")

if __name__ == '__main__':
    load_data()
