from django.urls import path
from .views import HostelListView, HostelCreateView, HostelUpdateView, HostelDeleteView

urlpatterns = [
    path('', HostelListView.as_view(), name='hostel_display'),
    path('add/', HostelCreateView.as_view(), name='hostel_add'),
    path('edit/<int:pk>/', HostelUpdateView.as_view(), name='hostel_edit'),
    path('delete/<int:pk>/', HostelDeleteView.as_view(), name='hostel_delete'),
]
