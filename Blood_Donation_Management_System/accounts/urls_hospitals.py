from django.urls import path
from . import views
urlpatterns = [
    path('', views.hospital_list, name='hospital_list'),
    path('add/', views.add_hospital, name='add_hospital'),
    path('edit/<int:pk>/', views.edit_hospital, name='edit_hospital'),
    path('delete/<int:pk>/', views.delete_hospital, name='delete_hospital'),
]
