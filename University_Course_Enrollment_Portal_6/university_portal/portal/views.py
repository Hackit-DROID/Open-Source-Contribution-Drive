from django.shortcuts import render
from django.db.models import Q
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