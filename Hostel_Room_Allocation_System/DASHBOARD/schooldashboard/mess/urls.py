from django.urls import path
from .views import MessListView, MessCreateView, MessUpdateView, MessDeleteView

urlpatterns = [
    path('', MessListView.as_view(), name='mess_display'),
    path('add/', MessCreateView.as_view(), name='mess_add'),
    path('edit/<int:pk>/', MessUpdateView.as_view(), name='mess_edit'),
    path('delete/<int:pk>/', MessDeleteView.as_view(), name='mess_delete'),
]
