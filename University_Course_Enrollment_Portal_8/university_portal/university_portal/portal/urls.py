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
    path('add-department/', views.add_department, name='add_department'),
    path('add-instructor/', views.add_instructor, name='add_instructor'),
    path('add-student/', views.add_student, name='add_student'),
    path('add-course/', views.add_course, name='add_course'),
    path('add-classroom/', views.add_classroom, name='add_classroom'),
    path('add-section/', views.add_section, name='add_section'),
    path('delete-department/<str:dept_name>/', views.delete_department, name='delete_department'),
    path('delete-instructor/<int:id>/', views.delete_instructor, name='delete_instructor'),
    path('delete-student/<int:id>/', views.delete_student, name='delete_student'),
    path('delete-course/<str:course_id>/', views.delete_course, name='delete_course'),
    path('delete-classroom/<int:id>/', views.delete_classroom, name='delete_classroom'),
    path('delete-section/<int:id>/', views.delete_section, name='delete_section'),
]