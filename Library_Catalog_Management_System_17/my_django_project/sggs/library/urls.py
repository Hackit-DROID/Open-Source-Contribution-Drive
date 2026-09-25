from django.urls import path
from . import views

urlpatterns = [
    path("show/", views.show_library, name="show_library"),
]
