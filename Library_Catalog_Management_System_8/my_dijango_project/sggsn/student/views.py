

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Student

# List + Search
def student_list(request):
    q = request.GET.get('q', '').strip()
    if q:
        students = Student.objects.filter(
            Q(name__icontains=q) | Q(regno__icontains=q) | Q(email__icontains=q)
        )
    else:
        students = Student.objects.all()
    return render(request, 'student/student_list.html', {'students': students, 'q': q})

# Detail view 👇 (this was missing!)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'student/student_detail.html', {'student': student})
