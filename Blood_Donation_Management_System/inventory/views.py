from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import BloodStock
from .forms import BloodStockForm

def is_hospital(user):
    return user.groups.filter(name='Hospital').exists()

@login_required
def stock_list(request):
    if request.user.is_superuser:
        stocks = BloodStock.objects.select_related('hospital').all()
    else:
        # hospital users see only their hospital stocks
        try:
            hp = request.user.hospital_profile
            stocks = BloodStock.objects.filter(hospital=hp)
        except:
            stocks = BloodStock.objects.none()
    return render(request, 'inventory/stock_list.html', {'stocks': stocks})

@login_required
@user_passes_test(is_hospital)
def add_stock(request):
    if request.method == 'POST':
        form = BloodStockForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stock_list')
    else:
        form = BloodStockForm()
    return render(request, 'inventory/stock_form.html', {'form': form})

@login_required
@user_passes_test(is_hospital)
def edit_stock(request, pk):
    stock = get_object_or_404(BloodStock, pk=pk)
    form = BloodStockForm(request.POST or None, instance=stock)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('stock_list')
    return render(request, 'inventory/stock_form.html', {'form': form})

@login_required
@user_passes_test(is_hospital)
def delete_stock(request, pk):
    stock = get_object_or_404(BloodStock, pk=pk)
    if request.method == 'POST':
        stock.delete()
        return redirect('stock_list')
    return render(request, 'inventory/stock_delete.html', {'stock': stock})
