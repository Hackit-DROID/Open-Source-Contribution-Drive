from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/books/', permanent=False)),
    path('users/', include('users.urls')),
    path('books/', include('books.urls')),
    path('transactions/', include('transactions.urls')),
    path('ai/', include('ai.urls')),
]
