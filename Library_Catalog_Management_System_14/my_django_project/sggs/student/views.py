from django.shortcuts import render, redirect, get_object_or_404
from .models import Student

# Show all students
def student_list(request):
    students = Student.objects.all()
    return render(request, 'student_list.html', {'students': students})

# Add a new student
def student_create(request):
    if request.method == 'POST':
        regno = request.POST.get('regno')
        name = request.POST.get('name')
        branch = request.POST.get('branch')
        year = request.POST.get('year')
        cet = request.POST.get('cet')

        Student.objects.create(
            regno=regno,
            name=name,
            branch=branch,
            year=year,
            cet=cet
        )
        return redirect('student_list')
    return render(request, 'student_form.html')

# Update student
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.regno = request.POST.get('regno')
        student.name = request.POST.get('name')
        student.branch = request.POST.get('branch')
        student.year = request.POST.get('year')
        student.cet = request.POST.get('cet')
        student.save()
        return redirect('student_list')
    return render(request, 'student_form.html', {'student': student})

# Delete student
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        return redirect('student_list')
    return render(request, 'student_confirm_delete.html', {'student': student})


# Create your views here.
