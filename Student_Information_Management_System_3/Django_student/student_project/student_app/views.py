
from django.shortcuts import render
from .models import Student

def student_list(request):
    # fetch all student records
    students = Student.objects.all()
    return render(request, 'students.html', {'students': students})

from django.shortcuts import render
from .models import Student

def toppers_view(request):
    students = Student.objects.all()

    # Calculate total marks for each student
    for s in students:
        s.total = s.phy + s.chem + s.math

    # Sort students by total marks descending
    top3 = sorted(students, key=lambda x: x.total, reverse=True)[:3]

    context = {
        'top3': top3
    }
    return render(request, 'show_topper.html', context)

def toppers(request):
    """
    Finds toppers by fetching all students and performing calculations
    and sorting in Python.
    """
    students = list(Student.objects.all()) # Get all students as a list

    overall_topper = None
    physics_topper = None
    chemistry_topper = None
    math_topper = None

    # Proceed only if there are students in the database
    if students:
        # 1. Calculate total marks for the Overall Topper
        # We add a 'total' attribute to each student object in the list
        for student in students:
            student.total = student.phy + student.chem + student.math
        
        # Find the student with the highest total using the max() function
        overall_topper = max(students, key=lambda s: s.total)

        # 2. Find Subject-wise Toppers
        # Find the student with the highest marks in each subject
        physics_topper = max(students, key=lambda s: s.phy)
        chemistry_topper = max(students, key=lambda s: s.chem)
        math_topper = max(students, key=lambda s: s.math)

    context = {
        'overall_topper': overall_topper,
        'physics_topper': physics_topper,
        'chemistry_topper': chemistry_topper,
        'math_topper': math_topper,
    }
    
    return render(request, 'show_topper.html', context)

def student_list(request):
    query = request.GET.get('q')  # get the search query from the URL
    if query:
        # Filter students by name or branch (case-insensitive)
        students = Student.objects.filter(
            student_name__icontains=query
        ) | Student.objects.filter(
            branch__icontains=query
        )
    else:
        # If no search, show all students
        students = Student.objects.all()

    context = {
        'students': students
    }
    return render(request, 'students.html', context)