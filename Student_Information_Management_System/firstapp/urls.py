from django.urls import path 
from . import views

urlpatterns = [
     path('admission/',views.admission,name='admission'),
     path('student/',views.student,name='student'),
     path('feedback/',views.feedback,name='feedback'),     
     path('marks/',views.mark,name='marks')    
]