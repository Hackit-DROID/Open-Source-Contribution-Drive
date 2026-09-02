from django.urls import path
from . import views

# urlpatterns = [
#     path("students/", views.student_list, name="student_list"),
#     path("toppers/", views.topper_view, name="topper_view"),
#     path("numpy/", views.view_numpy, name="view_numpy"),

# ]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                   # Home page
    path('students/', views.student_list, name='student_list'),
    path('toppers/', views.topper_view, name='topper_view'),
    path('search_name/', views.view_search_database_by_name, name='search_name'),
    path('numpy/', views.view_numpy, name='numpy'),
    path('sggs/', views.view_sggs, name='sggs'),
]
