
from django.contrib import admin
from django.urls import path, include
from . import views  
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('students.urls')),
    path('hostel/', include('hostel.urls')),
    path('mess/', include('mess.urls')),
    path('result/', include('result.urls')),
]