from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('student/', include('student.urls')),
    path('hostel/', include('hostel.urls')),
    path('account/', include('account.urls')),
    path('library/', include('library.urls')),
]
