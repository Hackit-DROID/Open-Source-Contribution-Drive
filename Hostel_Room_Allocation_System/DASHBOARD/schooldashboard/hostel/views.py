import csv
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Hostel
from .forms import HostelForm


class HostelListView(ListView):
    model = Hostel
    template_name = 'hostel/dashboard.html'
    context_object_name = 'hostels'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        block = self.request.GET.get('block', '').strip()
        sort = self.request.GET.get('sort', '').strip()

        if q:
            qs = qs.filter(
                Q(student_name__icontains=q) |
                Q(room_no__icontains=q) |
                Q(block__icontains=q) |
                Q(warden_name__icontains=q)
            )

        if status in ['Occupied', 'Vacant']:
            qs = qs.filter(status=status)

        if block:
            qs = qs.filter(block__iexact=block)

        allowed_sorts = {
            'room_no': 'room_no',
            '-room_no': '-room_no',
            'rent': 'rent',
            '-rent': '-rent',
            'student_name': 'student_name',
            '-student_name': '-student_name',
            'floor': 'floor',
            '-floor': '-floor',
        }
        if sort in allowed_sorts:
            qs = qs.order_by(allowed_sorts[sort])
        else:
            qs = qs.order_by('block', 'floor', 'room_no')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_hostels = Hostel.objects.all()

        total_rooms = all_hostels.count()
        occupied_rooms = all_hostels.filter(status='Occupied').count()
        vacant_rooms = all_hostels.filter(status='Vacant').count()
        total_rent = all_hostels.filter(status='Occupied').aggregate(total=Sum('rent'))['total'] or 0
        occupancy_rate = round((occupied_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0

        context['total_rooms'] = total_rooms
        context['occupied_rooms'] = occupied_rooms
        context['vacant_rooms'] = vacant_rooms
        context['total_rent'] = total_rent
        context['occupancy_rate'] = occupancy_rate
        context['blocks'] = (
            Hostel.objects.values_list('block', flat=True)
            .distinct()
            .order_by('block')
        )

        # Retain query parameters for pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()

        context['current_q'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_block'] = self.request.GET.get('block', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context


class HostelCreateView(SuccessMessageMixin, CreateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'hostel/form.html'
    success_url = reverse_lazy('hostel_display')
    success_message = "Hostel room allocation for %(student_name)s (Room %(room_no)s) created successfully!"


class HostelUpdateView(SuccessMessageMixin, UpdateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'hostel/form.html'
    success_url = reverse_lazy('hostel_display')
    success_message = "Hostel record for Room %(room_no)s updated successfully!"


class HostelDeleteView(DeleteView):
    model = Hostel
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel_display')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        room_no = obj.room_no
        messages.success(request, f"Hostel record for Room {room_no} was successfully deleted.")
        return super().delete(request, *args, **kwargs)


def export_hostels_csv(request):
    """Exports hostel allocations to a downloadable CSV file."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hostel_allocations.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Student Name', 'Room No', 'Block', 'Floor', 'Warden Name', 'Rent (INR)', 'Status'])

    hostels = Hostel.objects.all().order_by('block', 'floor', 'room_no')
    for h in hostels:
        writer.writerow([h.id, h.student_name, h.room_no, h.block, h.floor, h.warden_name, h.rent, h.status])

    return response


def vacate_hostel_room(request, pk):
    """Quick 1-click action to vacate an occupied hostel room."""
    if request.method == 'POST':
        hostel = get_object_or_404(Hostel, pk=pk)
        old_student = hostel.student_name
        hostel.status = 'Vacant'
        hostel.student_name = f"Vacant (Prev: {old_student})"
        hostel.save()
        messages.success(request, f"Room {hostel.room_no} has been vacated successfully.")
    return redirect('hostel_display')

