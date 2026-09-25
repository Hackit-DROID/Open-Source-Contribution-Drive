from django.shortcuts import render
from django.db.models import Q
from .models import Student


def show_students(request):
    # Get search query and sort field from GET parameters
    search_query = request.GET.get("q", "")
    sort_by = request.GET.get("sort", "regno")

    # Start with all students
    students = Student.objects.all()

    # 🔍 Search filter (checks name, regno, branch)
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) |
            Q(regno__icontains=search_query) |
            Q(branch__icontains=search_query)
        )

    # ✅ Whitelist allowed fields for sorting
    allowed_sort_fields = ["name", "regno", "branch", "year", "cet"]
    if sort_by in allowed_sort_fields:
        students = students.order_by(sort_by)

    return render(request, "show_students.html", {
        "students": students,
        "search_query": search_query,
        "sort_by": sort_by,
    })
