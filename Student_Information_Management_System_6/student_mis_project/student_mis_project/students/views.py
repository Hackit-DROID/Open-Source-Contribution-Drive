# students/views.py

from django.shortcuts import render
from .models import Student

def student_list(request):
    # Get all student objects from the database
    students = Student.objects.all()
    # Create a context dictionary to pass the data to the template
    context = {
        'students': students
    }
    # Render the request, template, and context
    return render(request, 'students/student_list.html', context)