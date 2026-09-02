from django.shortcuts import render
from django.db.models import Q
from .models import Hostel

def show_hostels(request):
    # 🔎 search query
    search_query = request.GET.get("q", "")
    sort_by = request.GET.get("sort", "regno")  # default sorting by regno

    hostels = Hostel.objects.all()

    if search_query:
        hostels = hostels.filter(
            Q(regno__icontains=search_query) |
            Q(hostel_name__icontains=search_query) |
            Q(room_no__icontains=search_query)
        )

    # ⬆️⬇️ sorting
    hostels = hostels.order_by(sort_by)

    return render(
        request,
        "show_hostels.html",
        {"hostels": hostels, "search_query": search_query}
    )
