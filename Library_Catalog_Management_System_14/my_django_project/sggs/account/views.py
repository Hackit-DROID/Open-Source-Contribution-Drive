from django.shortcuts import render, redirect, get_object_or_404
from .models import Account

def account_list(request):
    accounts = Account.objects.all()
    return render(request, 'account_list.html', {'accounts': accounts})

def account_create(request):
    if request.method == 'POST':
        Account.objects.create(
            regno=request.POST.get('regno'),
            fees_type=request.POST.get('fees_type'),
            amount=request.POST.get('amount'),
        )
        return redirect('account_list')
    return render(request, 'account_form.html')

def account_update(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        account.regno = request.POST.get('regno')
        account.fees_type = request.POST.get('fees_type')
        account.amount = request.POST.get('amount')
        account.save()
        return redirect('account_list')
    return render(request, 'account_form.html', {'account': account})

def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        account.delete()
        return redirect('account_list')
    return render(request, 'account_confirm_delete.html', {'account': account})


# Create your views here.
