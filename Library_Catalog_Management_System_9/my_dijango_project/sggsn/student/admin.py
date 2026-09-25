
 
# Register your models here.
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib import admin
from .models import Student

class StudentAdmin(admin.ModelAdmin):
    list_display = ['regno', 'name', 'department', 'phy', 'chem', 'math']
    search_fields = ['name']
    list_filter = ['department']

admin.site.register(Student, StudentAdmin)


# def student_list(request):
#     q = request.GET.get('q', '').strip()   # search query from URL ?q=...
#     if q:
#         # search by name OR regno OR email (partial, case-insensitive)
#         students = Student.objects.filter(
#             Q(name__icontains=q) | Q(regno__icontains=q) | Q(email__icontains=q)
#         )
#     else:
#         students = Student.objects.all()
#     return render(request, 'student/student_list.html', {
#         'students': students,
#         'q': q,
#     })

# def student_detail(request, pk):
#     student = get_object_or_404(Student, pk=pk)
#     return render(request, 'student/student_detail.html', {'student': student})
