from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_list, name='library_list'),
    path('create/', views.library_create, name='library_create'),
    path('update/<int:pk>/', views.library_update, name='library_update'),
    path('delete/<int:pk>/', views.library_delete, name='library_delete'),
]
