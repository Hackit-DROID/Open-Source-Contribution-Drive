from django.urls import path
from . import views

urlpatterns = [
    path('', views.HostelListView.as_view(), name='hostel_display'),
    path('add/', views.HostelCreateView.as_view(), name='hostel_add'),
    path('edit/<int:pk>/', views.HostelUpdateView.as_view(), name='hostel_edit'),
    path('delete/<int:pk>/', views.HostelDeleteView.as_view(), name='hostel_delete'),
    path('vacate/<int:pk>/', views.vacate_hostel_room, name='hostel_vacate'),
    path('export/csv/', views.export_hostels_csv, name='hostel_export_csv'),
]

