from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('instructors/', views.instructors_list, name='instructors_list'),
    path('search/', views.search, name='search'),
    path('courses/', views.courses_list, name='courses_list'),
    path('students/', views.students_list, name='students_list'),
    path('departments/', views.departments_list, name='departments_list'),
    path('classrooms/', views.classrooms_list, name='classrooms_list'),
    path('sections/', views.sections_timetable, name='sections_timetable'),
]