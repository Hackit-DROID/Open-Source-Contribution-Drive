
from django.shortcuts import render
from .models import Library

def library_list(request):
    libraries = Library.objects.all()
    return render(request, 'library_list.html', {'libraries': libraries})
