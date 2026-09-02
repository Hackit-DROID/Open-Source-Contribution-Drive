from django.contrib import admin
from django.urls import path
from student_app import views   # import views from the app
from django.db.models import F

urlpatterns = [
    path('admin/', admin.site.urls),
    path('students/', views.student_list, name='student_list'),  # direct route
    path('toppers/', views.toppers_view, name='toppers'),  # New page
    # Add the new path for the toppers page
    path('toppers1/', views.toppers, name='toppers'),

]
