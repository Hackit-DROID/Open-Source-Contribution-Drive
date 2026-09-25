# student/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('show/', views.show_students, name='show_students'),
]
