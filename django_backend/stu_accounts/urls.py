from django.urls import path
from . import views

urlpatterns = [
    path('auth/login', views.login_api, name='api_login'),
    path('auth/logout', views.logout_api, name='api_logout'),
    path('auth/register', views.register_api, name='api_register'),
    path('student/bonus/add', views.add_bonus_api, name='api_student_bonus_add'),
    path('student/bonus/reset',views.reset_bonus_api,name = 'api_student_bonus_reset')
]
