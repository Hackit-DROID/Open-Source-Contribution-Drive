from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path('issue/<int:book_id>/', views.issue_book, name='issue'),
    path('return/<int:issue_id>/', views.return_book, name='return'),
    path('my-books/', views.my_books, name='my_books'),
    path('all/', views.all_issues, name='all_issues'),
]
