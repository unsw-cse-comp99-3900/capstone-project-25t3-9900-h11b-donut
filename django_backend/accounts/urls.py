from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # 对应 "/"
    path('register', views.register, name='register'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('welcome', views.welcome, name='welcome'),
]
