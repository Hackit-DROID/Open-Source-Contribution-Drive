from django.urls import path
from . import views

urlpatterns = [
    path('', views.hostel_list, name='hostel_list'),
]
