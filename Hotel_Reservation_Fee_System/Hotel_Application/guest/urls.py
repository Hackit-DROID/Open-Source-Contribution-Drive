from django.urls import path
from . import views

urlpatterns = [
    path("guests/", views.guest_list, name="guest_list"),
]


