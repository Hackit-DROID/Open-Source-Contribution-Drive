from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page
    path('', lambda request: render(request, 'index.html'), name='home'),

    # Include all URLs from the students app
    path('students/', include('students.urls')),
]
