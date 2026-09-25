from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Homepage
    path('students/', views.all_students, name='all_students'),
    path('toppers/', views.toppers, name='toppers'),
    path('student-reports/', views.student_reports, name='student_reports'),
    path('numpy-methods/', views.numpy_methods, name='numpy_methods'),  # New NumPy page
]
