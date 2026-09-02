from django.shortcuts import render
from .models import Account

def account_list(request):
    """
    View to list all student accounts
    """
    accounts = Account.objects.all()
    return render(request, 'account/account_list.html', {'accounts': accounts})
