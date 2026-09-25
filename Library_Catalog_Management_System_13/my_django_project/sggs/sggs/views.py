from django.shortcuts import render
from student.models import Student
from hostel.models import Hostel
from library.models import Library
from account.models import Account
from faculty.models import Faculty
from django.db.models import F, FloatField, ExpressionWrapper

def dashboard(request):
    # Counts
    total_students = Student.objects.count()
    total_hostels = Hostel.objects.count()
    total_books = Library.objects.count()
    total_accounts = Account.objects.count()
    total_faculty = Faculty.objects.count()

    # Toppers (top 1 student for each subject)
    physics_topper = Student.objects.order_by('-physics').first()
    chemistry_topper = Student.objects.order_by('-chemistry').first()
    maths_topper = Student.objects.order_by('-maths').first()

    # Latest 5 entries
    students = Student.objects.all().order_by('-id')[:5]
    hostels = Hostel.objects.all().order_by('-id')[:5]
    books = Library.objects.all().order_by('-id')[:5]
    accounts = Account.objects.all().order_by('-id')[:5]
    faculties = Faculty.objects.all().order_by('-id')[:5]

    context = {
        'total_students': total_students,
        'total_hostels': total_hostels,
        'total_books': total_books,
        'total_accounts': total_accounts,
        'total_faculty': total_faculty,
        'physics_topper': physics_topper,
        'chemistry_topper': chemistry_topper,
        'maths_topper': maths_topper,
        'students': students,
        'hostels': hostels,
        'books': books,
        'accounts': accounts,
        'faculties': faculties,
    }

    return render(request, 'dashboard.html', context)

def students(request):
    query = request.GET.get('q')
    if query:
        students = Student.objects.filter(name__icontains=query)
    else:
        students = Student.objects.all()
    return render(request, 'students.html', {'students': students, 'query': query})

def hostels(request):
    return render(request, 'hostels.html', {'hostels': Hostel.objects.all()})

def books(request):
    return render(request, 'books.html', {'books': Library.objects.all()})

def accounts(request):
    return render(request, 'accounts.html', {'accounts': Account.objects.all()})

def faculty(request):
    return render(request, 'faculty.html', {'faculties': Faculty.objects.all()})
