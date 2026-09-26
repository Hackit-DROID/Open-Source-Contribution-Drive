from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Hostel
from .forms import HostelForm
from .clearance_engine import (
    HostelCheckOutClearanceEngine,
    DamageAssessment,
    ClearanceCertificate,
)

class HostelListView(ListView):
    model = Hostel
    template_name = 'hostel/dashboard.html'
    context_object_name = 'hostels'

class HostelCreateView(CreateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'hostel/form.html'
    success_url = reverse_lazy('hostel_display')

class HostelUpdateView(UpdateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'hostel/form.html'
    success_url = reverse_lazy('hostel_display')

class HostelDeleteView(DeleteView):
    model = Hostel
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel_display')


def checkout_clearance_view(request, pk):
    """Process student hostel checkout clearance, compute net refund, and set status to 'Checked Out'."""
    hostel = get_object_or_404(Hostel, pk=pk)

    try:
        initial_deposit = float(request.POST.get('initial_deposit', request.GET.get('initial_deposit', 500.0)))
        unpaid_mess = float(request.POST.get('unpaid_mess_bills', request.GET.get('unpaid_mess_bills', 0.0)))
        damage_fee = float(request.POST.get('damage_fee', request.GET.get('damage_fee', 0.0)))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid financial parameter values provided."}, status=400)

    damages = []
    if damage_fee > 0:
        damages.append(DamageAssessment(
            damage_id="DMG-001",
            description=request.POST.get('damage_desc', request.GET.get('damage_desc', 'Room fixture damage')),
            fee=damage_fee,
        ))

    engine = HostelCheckOutClearanceEngine()
    certificate = engine.process_checkout_clearance(
        student_name=hostel.student_name,
        room_no=hostel.room_no,
        initial_deposit=initial_deposit,
        unpaid_mess_bills=unpaid_mess,
        damage_assessments=damages,
        hostel_record=hostel,
    )

    return JsonResponse(certificate.to_dict())
