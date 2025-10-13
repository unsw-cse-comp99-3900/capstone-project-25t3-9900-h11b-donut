from django.urls import path
from . import views

urlpatterns = [
    path('auth/login', views.login_api, name='api_login'),
    path('auth/logout', views.logout_api, name='api_logout'),
    path('auth/register', views.register_api, name='api_register'),
    #下面是老的
    path('', views.index, name='index'),  # 对应 "/"
    path('welcome', views.welcome, name='welcome'),
]
