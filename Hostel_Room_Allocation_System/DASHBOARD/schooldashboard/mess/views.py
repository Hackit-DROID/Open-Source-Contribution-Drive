from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Mess
from .forms import MessForm

class MessListView(ListView):
    model = Mess
    template_name = 'mess/dashboard.html'
    context_object_name = 'meals'

class MessCreateView(CreateView):
    model = Mess
    form_class = MessForm
    template_name = 'mess/form.html'
    success_url = reverse_lazy('mess_display')

class MessUpdateView(UpdateView):
    model = Mess
    form_class = MessForm
    template_name = 'mess/form.html'
    success_url = reverse_lazy('mess_display')

class MessDeleteView(DeleteView):
    model = Mess
    template_name = 'mess/confirm_delete.html'
    success_url = reverse_lazy('mess_display')
