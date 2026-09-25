
from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('view_student/',views.view_student),
   # path('numpy/',views.view_numpy),
    path('show_toppers/',views.show_toppers,name='show_toppers'),
    path('hello_user/',views.hello_user,name='hello_user'),
    path('view_numpy/',views.view_numpy,name='view_numpy'),
    path('search_student/',views.search_student,name='search_student'),
    path('',views.home,name='home'),
    path('home/', views.home, name='home_page'),

]
