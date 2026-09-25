from django.shortcuts import render
from student.models import Student
from library.models import Library
from account.models import Account
from hostel.models import Hostel

def show_all(request):
    students = Student.objects.all()
    library = Library.objects.all()
    accounts = Account.objects.all()
    hostels = Hostel.objects.all()

    context = {
        "students": students,
        "library": library,
        "accounts": accounts,
        "hostels": hostels
    }
    return render(request, "show.html", context)
