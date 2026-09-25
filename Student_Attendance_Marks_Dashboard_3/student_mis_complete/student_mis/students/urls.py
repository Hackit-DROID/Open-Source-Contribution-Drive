from django.urls import path
from . import views

urlpatterns = [
    # Home and Authentication
    path('', views.home, name='home'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('student-login/', views.student_login, name='student_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin Panel
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/students/', views.student_list, name='student_list'),
    path('dashboard/students/add/', views.add_student, name='add_student'),
    path('dashboard/students/edit/<str:reg_no>/', views.edit_student, name='edit_student'),
    path('dashboard/students/delete/<str:reg_no>/', views.delete_student, name='delete_student'),
    path('dashboard/students/marks/<str:reg_no>/', views.add_marks, name='add_marks'),
    path('dashboard/students/attendance/<str:reg_no>/', views.add_attendance, name='add_attendance'),
    path('dashboard/students/report/<str:reg_no>/', views.view_report, name='view_report'),
    
    # Student Panel
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]
