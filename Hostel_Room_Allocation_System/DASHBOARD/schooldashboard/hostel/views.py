from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Hostel
from .forms import HostelForm

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
