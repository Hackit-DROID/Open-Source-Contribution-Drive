from django.shortcuts import render

from .models import Account, Hostel, Library

def home(request):
    accounts = Account.objects.all()
    hostels = Hostel.objects.all()
    libraries = Library.objects.all()
    return render(request, "home.html", {
        "accounts": accounts,
        "hostels": hostels,
        "libraries": libraries
    })
