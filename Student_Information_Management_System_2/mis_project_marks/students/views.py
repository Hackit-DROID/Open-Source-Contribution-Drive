from django.shortcuts import render
from .models import Student
import numpy as np

# ------------------- Config -------------------
# branches shown in the filter dropdowns
BRANCHES = ['CSE', 'IT', 'ECE', 'EEE']

# minimum average needed for each grade, checked top to bottom
GRADE_CUTOFFS = [
    (90, 'A+'),
    (80, 'A'),
    (70, 'B'),
    (60, 'C'),
]
FAIL_GRADE = 'F'

# decimal places used when showing averages
AVG_DECIMALS = 2


def get_grade(average):
    for cutoff, grade in GRADE_CUTOFFS:
        if average >= cutoff:
            return grade
    return FAIL_GRADE


# ------------------- Homepage / Index -------------------
def index(request):
    return render(request, 'students/index.html')


# ------------------- All Students -------------------
def all_students(request):
    students = Student.objects.all()
    
    # Search by name or regno
    query = request.GET.get('search')
    if query:
        students = students.filter(student_name__icontains=query) | students.filter(regno__icontains=query)
    
    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        students = students.filter(branch=branch_filter)

    return render(request, 'students/all_students.html', {'students': students, 'branches': BRANCHES})


# ------------------- Toppers -------------------
def toppers(request):
    students = Student.objects.all()

    phy_topper = Student.objects.order_by('-phy').first()
    chem_topper = Student.objects.order_by('-chem').first()
    math_topper = Student.objects.order_by('-math').first()

    class_topper = None
    class_topper_avg = 0
    if students.exists():
        class_topper = max(students, key=lambda s: (s.phy + s.chem + s.math)/3)
        class_topper_avg = round((class_topper.phy + class_topper.chem + class_topper.math)/3, AVG_DECIMALS)

    context = {
        'phy_topper': phy_topper,
        'chem_topper': chem_topper,
        'math_topper': math_topper,
        'class_topper': class_topper,
        'class_topper_avg': class_topper_avg,
    }

    return render(request, 'students/toppers.html', context)


# ------------------- Student Reports -------------------
def student_reports(request):
    students = Student.objects.all()

    # Search by name or regno
    query = request.GET.get('search')
    if query:
        students = students.filter(student_name__icontains=query) | students.filter(regno__icontains=query)

    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        students = students.filter(branch=branch_filter)

    # Calculate average & grade for each student
    for student in students:
        student.average = round((student.phy + student.chem + student.math) / 3, AVG_DECIMALS)
        student.grade = get_grade(student.average)

    # Class subject averages
    if students.exists():
        class_avg_phy = round(sum(s.phy for s in students) / students.count(), AVG_DECIMALS)
        class_avg_chem = round(sum(s.chem for s in students) / students.count(), AVG_DECIMALS)
        class_avg_math = round(sum(s.math for s in students) / students.count(), AVG_DECIMALS)
    else:
        class_avg_phy = class_avg_chem = class_avg_math = 0

    context = {
        'students': students,
        'class_avg_phy': class_avg_phy,
        'class_avg_chem': class_avg_chem,
        'class_avg_math': class_avg_math,
        'branches': BRANCHES,
    }

    return render(request, 'students/student_reports.html', context)


# ------------------- NumPy Methods -------------------
def numpy_methods(request):
    import numpy as np

    # Get all callable methods from numpy
    all_numpy = dir(np)
    methods = [m for m in all_numpy if callable(getattr(np, m))]

    # Search filter for methods
    search_query = request.GET.get('search')
    if search_query:
        methods = [m for m in methods if search_query.lower() in m.lower()]

    context = {
        'methods': methods,
        'search_query': search_query or '',
    }

    return render(request, 'students/numpy_methods.html', context)