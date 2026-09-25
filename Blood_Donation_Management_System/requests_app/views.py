from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import BloodRequestForm
from .models import BloodRequest
def is_hospital(user):
    return user.groups.filter(name='Hospital').exists()

@login_required
def request_list(request):
    if request.user.is_superuser:
        reqs = BloodRequest.objects.select_related('hospital').all()
    else:
        try:
            reqs = BloodRequest.objects.filter(hospital=request.user.hospital_profile)
        except:
            reqs = BloodRequest.objects.none()
    return render(request, 'requests_app/request_list.html', {'reqs': reqs})

@login_required
@user_passes_test(is_hospital)
def add_request(request):
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('request_list')
    else:
        form = BloodRequestForm()
    return render(request, 'requests_app/add_request.html', {'form': form})
