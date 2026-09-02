from django.shortcuts import render
from django.db.models import Q
from .models import Account


def show_accounts(request):
    # Get search & sort values from query parameters
    search_query = request.GET.get("q", "")
    sort_by = request.GET.get("sort", "regno")  # default sort

    # Start with all accounts
    accounts = Account.objects.all()

    # 🔍 Search filter (Reg No, Fees Type, Amount)
    if search_query:
        accounts = accounts.filter(
            Q(regno__icontains=search_query) |
            Q(fees_type__icontains=search_query) |
            Q(amount__icontains=search_query)
        )

    # ✅ Allowed sort fields to avoid errors
    allowed_sort_fields = ["regno", "fees_type", "amount"]
    if sort_by in allowed_sort_fields:
        accounts = accounts.order_by(sort_by)

    return render(request, "show_accounts.html", {
        "accounts": accounts,
        "search_query": search_query,
        "sort_by": sort_by,
    })
