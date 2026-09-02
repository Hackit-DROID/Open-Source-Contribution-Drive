from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import DonorForm, DonationForm
from .models import Donor, Donation
def is_hospital(user):
    return user.groups.filter(name='Hospital').exists()

@login_required
def donor_list(request):
    donors = Donor.objects.all()
    return render(request, 'donations/donor_list.html', {'donors': donors})

@login_required
@user_passes_test(is_hospital)
def add_donor(request):
    if request.method == 'POST':
        form = DonorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('donor_list')
    else:
        form = DonorForm()
    return render(request, 'donations/add_donor.html', {'form': form})

@login_required
def edit_donor(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    form = DonorForm(request.POST or None, instance=donor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('donor_list')
    return render(request, 'donations/add_donor.html', {'form': form})

@login_required
def delete_donor(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    if request.method == 'POST':
        donor.delete()
        return redirect('donor_list')
    return render(request, 'donations/confirm_delete.html', {'donor': donor})

@login_required
def donation_list(request):
    if request.user.is_superuser:
        donations = Donation.objects.select_related('donor','hospital').all()
    else:
        try:
            donations = Donation.objects.filter(hospital=request.user.hospital_profile)
        except:
            donations = Donation.objects.none()
    return render(request, 'donations/donation_list.html', {'donations': donations})

@login_required
@user_passes_test(is_hospital)
def add_donation(request):
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.hospital = request.user.hospital_profile
            donation.save()
            return redirect('donation_list')
    else:
        form = DonationForm()
    return render(request, 'donations/add_donation.html', {'form': form})
