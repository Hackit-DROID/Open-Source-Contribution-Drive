from django.urls import path
from . import views

urlpatterns = [
    path("show/", views.show_hostels, name="show_hostels"),
]
