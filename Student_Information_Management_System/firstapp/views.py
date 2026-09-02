from django.shortcuts import render
from django.http import HttpResponse
from .models import Student,Admission,marks,Feedback
# Create your views here.

   # return HttpResponse("hello")
# Create your views here.
def admission(request):
    event_list=Admission.objects.all()
    return render(request,'admission.html',{'event_list':event_list})

def student(request):
    event_list=Student.objects.all()
    return render(request,'student.html',{'event_list':event_list})

def feedback(request):
    event_list=Feedback.objects.all()
    return render(request,'feedback.html',{'event_list':event_list})

def mark(request):
    event_list=marks.objects.all()
    return render(request,'marks.html',{'event_list':event_list})