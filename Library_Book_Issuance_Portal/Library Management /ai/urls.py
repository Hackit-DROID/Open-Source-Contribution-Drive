from django.urls import path

from . import views

app_name = 'ai'

urlpatterns = [
    path('chat/', views.chat_page, name='chat'),
    path('chat/ask/', views.chat_ask, name='chat_ask'),
]
