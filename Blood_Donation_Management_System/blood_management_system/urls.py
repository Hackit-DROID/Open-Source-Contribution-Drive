from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('accounts.urls')),
    path('hospitals/', include('accounts.urls_hospitals')),
    path('stocks/', include('inventory.urls')),
    path('donors/', include('donations.urls_donors')),
    path('donations/', include('donations.urls')),
    path('requests/', include('requests_app.urls')),
]
