from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from .models import HospitalProfile
from inventory.models import BloodStock
from .forms import HospitalForm

@login_required
def home(request):
    return redirect('dashboard')

@login_required
def dashboard(request):
    data = BloodStock.objects.values('blood_group').annotate(total_units=Sum('units')).order_by('blood_group')
    stocks = BloodStock.objects.select_related('hospital').all()
    return render(request, 'accounts/dashboard.html', {'data': data, 'stocks': stocks})

def is_super(user):
    return user.is_superuser

@login_required
def hospital_list(request):
    if request.user.is_superuser:
        hospitals = HospitalProfile.objects.all()
    else:
        hospitals = HospitalProfile.objects.filter(user=request.user)
    return render(request, 'accounts/hospital_list.html', {'hospitals': hospitals})

@login_required
@user_passes_test(is_super)
def add_hospital(request):
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hospital_list')
    else:
        form = HospitalForm()
    return render(request, 'accounts/hospital_form.html', {'form': form})

@login_required
@user_passes_test(is_super)
def edit_hospital(request, pk):
    h = get_object_or_404(HospitalProfile, pk=pk)
    form = HospitalForm(request.POST or None, instance=h)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('hospital_list')
    return render(request, 'accounts/hospital_form.html', {'form': form})

@login_required
@user_passes_test(is_super)
def delete_hospital(request, pk):
    h = get_object_or_404(HospitalProfile, pk=pk)
    if request.method == 'POST':
        h.delete()
        return redirect('hospital_list')
    return render(request, 'accounts/hospital_delete.html', {'h': h})
