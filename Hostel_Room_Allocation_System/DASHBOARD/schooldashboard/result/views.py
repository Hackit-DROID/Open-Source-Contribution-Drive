from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Result
from .forms import ResultForm

class ResultListView(ListView):
    model = Result
    template_name = 'result/dashboard.html'
    context_object_name = 'results'

class ResultCreateView(CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'result/form.html'
    success_url = reverse_lazy('result_display')

class ResultUpdateView(UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'result/form.html'
    success_url = reverse_lazy('result_display')

class ResultDeleteView(DeleteView):
    model = Result
    template_name = 'result/confirm_delete.html'
    success_url = reverse_lazy('result_display')
