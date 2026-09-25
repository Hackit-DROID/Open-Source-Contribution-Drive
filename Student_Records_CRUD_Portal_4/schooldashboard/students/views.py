from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Student
from .forms import StudentForm

class StudentListView(ListView):
    model = Student
    template_name = 'students/dashboard.html'
    context_object_name = 'students'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        sort = self.request.GET.get('sort')
        if q:
            qs = qs.filter(name__icontains=q)
        if sort:
            qs = qs.order_by(sort)
        return qs

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('display')

class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('display')

class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'students/confirm_delete.html'
    success_url = reverse_lazy('display')
