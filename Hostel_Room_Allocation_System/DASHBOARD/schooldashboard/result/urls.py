from django.urls import path
from .views import ResultListView, ResultCreateView, ResultUpdateView, ResultDeleteView

urlpatterns = [
    path('', ResultListView.as_view(), name='result_display'),
    path('add/', ResultCreateView.as_view(), name='result_add'),
    path('edit/<int:pk>/', ResultUpdateView.as_view(), name='result_edit'),
    path('delete/<int:pk>/', ResultDeleteView.as_view(), name='result_delete'),
]
