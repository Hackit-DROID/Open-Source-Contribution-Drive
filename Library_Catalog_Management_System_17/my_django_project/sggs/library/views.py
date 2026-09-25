from django.shortcuts import render
from .models import Library
from django.db.models import Q

def show_library(request):
    # get search and sort parameters from query string
    search_query = request.GET.get("q", "")
    sort_by = request.GET.get("sort", "book_name")   # default sort by book_name

    libraries = Library.objects.all()

    # 🔍 Search logic
    if search_query:
        libraries = libraries.filter(
            Q(regno__icontains=search_query) |
            Q(book_name__icontains=search_query) |
            Q(date_issue__icontains=search_query) |
            Q(date_return__icontains=search_query)
        )

    # 🔽 Sorting logic
    libraries = libraries.order_by(sort_by)

    return render(
        request,
        "show_library.html",
        {"libraries": libraries, "search_query": search_query}
    )
