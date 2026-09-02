from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from .models import *

def home(request):
    return render(request, 'portal/home.html')

def instructors_list(request):
    instructors_courses = []
    instructors = Instructor.objects.all()
    
    for instructor in instructors:
        teaches_records = Teaches.objects.filter(ID=instructor)
        courses = [teach.course_id for teach in teaches_records]
        instructors_courses.append({
            'instructor': instructor,
            'courses': courses
        })
    
    return render(request, 'portal/instructors_list.html', {
        'instructors_courses': instructors_courses
    })

def search(request):
    search_type = request.GET.get('type', 'instructors')
    query = request.GET.get('query', '')
    results = []
    
    if query:
        if search_type == 'instructors':
            results = Instructor.objects.filter(
                Q(name__icontains=query) | Q(dept_name__dept_name__icontains=query)
            ).select_related('dept_name')
        elif search_type == 'students':
            results = Student.objects.filter(
                Q(name__icontains=query) | Q(dept_name__dept_name__icontains=query)
            ).select_related('dept_name')
        elif search_type == 'courses':
            results = Course.objects.filter(
                Q(course_id__icontains=query) | Q(title__icontains=query) | Q(dept_name__dept_name__icontains=query)
            ).select_related('dept_name')
        elif search_type == 'departments':
            results = Department.objects.filter(
                Q(dept_name__icontains=query) | Q(building__icontains=query)
            )
    
    return render(request, 'portal/search.html', {
        'results': results,
        'query': query,
        'search_type': search_type
    })

def courses_list(request):
    courses = Course.objects.select_related('dept_name').all()
    return render(request, 'portal/courses_list.html', {'courses': courses})

def students_list(request):
    students = Student.objects.select_related('dept_name').all()
    return render(request, 'portal/students_list.html', {'students': students})

def departments_list(request):
    departments = Department.objects.all()
    return render(request, 'portal/departments_list.html', {'departments': departments})

def classrooms_list(request):
    classrooms = Classroom.objects.all().order_by('building', 'room_no')
    return render(request, 'portal/classrooms_list.html', {'classrooms': classrooms})

def sections_timetable(request):
    sections = Section.objects.select_related('course_id').all()
    sections_data = []
    
    for section in sections:
        try:
            time_slot = TimeSlot.objects.filter(time_slot_id=section.time_slot_id).first()
            sections_data.append({
                'section': section,
                'time_slot': time_slot
            })
        except:
            sections_data.append({
                'section': section,
                'time_slot': None
            })
    
    return render(request, 'portal/sections_timetable.html', {'sections_data': sections_data})

def add_department(request):
    if request.method == 'POST':
        Department.objects.create(
            dept_name=request.POST['dept_name'],
            building=request.POST['building'],
            budget=int(request.POST['budget'])
        )
        messages.success(request, 'Department added successfully!')
        return redirect('departments_list')
    return render(request, 'portal/add_department.html')

def add_instructor(request):
    if request.method == 'POST':
        Instructor.objects.create(
            ID=int(request.POST['ID']),
            name=request.POST['name'],
            dept_name_id=request.POST['dept_name'],
            salary=int(request.POST['salary'])
        )
        messages.success(request, 'Instructor added successfully!')
        return redirect('instructors_list')
    departments = Department.objects.all()
    return render(request, 'portal/add_instructor.html', {'departments': departments})

def add_student(request):
    if request.method == 'POST':
        Student.objects.create(
            ID=int(request.POST['ID']),
            name=request.POST['name'],
            dept_name_id=request.POST['dept_name'],
            tot_cred=int(request.POST['tot_cred'])
        )
        messages.success(request, 'Student added successfully!')
        return redirect('students_list')
    departments = Department.objects.all()
    return render(request, 'portal/add_student.html', {'departments': departments})

def add_course(request):
    if request.method == 'POST':
        Course.objects.create(
            course_id=request.POST['course_id'],
            title=request.POST['title'],
            dept_name_id=request.POST['dept_name'],
            credits=int(request.POST['credits'])
        )
        messages.success(request, 'Course added successfully!')
        return redirect('courses_list')
    departments = Department.objects.all()
    return render(request, 'portal/add_course.html', {'departments': departments})

def add_classroom(request):
    if request.method == 'POST':
        Classroom.objects.create(
            building=request.POST['building'],
            room_no=request.POST['room_no'],
            capacity=int(request.POST['capacity'])
        )
        messages.success(request, 'Classroom added successfully!')
        return redirect('classrooms_list')
    return render(request, 'portal/add_classroom.html')

def add_section(request):
    if request.method == 'POST':
        Section.objects.create(
            course_id_id=request.POST['course_id'],
            sec_id=request.POST['sec_id'],
            semester=request.POST['semester'],
            year=int(request.POST['year']),
            building=request.POST['building'],
            room_no=request.POST['room_no'],
            time_slot_id=int(request.POST['time_slot_id'])
        )
        messages.success(request, 'Section added successfully!')
        return redirect('sections_timetable')
    courses = Course.objects.all()
    return render(request, 'portal/add_section.html', {'courses': courses})

def delete_department(request, dept_name):
    Department.objects.get(dept_name=dept_name).delete()
    messages.success(request, 'Department deleted successfully!')
    return redirect('departments_list')

def delete_instructor(request, id):
    Instructor.objects.get(ID=id).delete()
    messages.success(request, 'Instructor deleted successfully!')
    return redirect('instructors_list')

def delete_student(request, id):
    Student.objects.get(ID=id).delete()
    messages.success(request, 'Student deleted successfully!')
    return redirect('students_list')

def delete_course(request, course_id):
    Course.objects.get(course_id=course_id).delete()
    messages.success(request, 'Course deleted successfully!')
    return redirect('courses_list')

def delete_classroom(request, id):
    Classroom.objects.get(id=id).delete()
    messages.success(request, 'Classroom deleted successfully!')
    return redirect('classrooms_list')

def delete_section(request, id):
    Section.objects.get(id=id).delete()
    messages.success(request, 'Section deleted successfully!')
    return redirect('sections_timetable')