from django.urls import path
from . import views

urlpatterns = [
    path("register", views.register_admin, name="admin_register"),
    path("login", views.login_admin, name="admin_login"),
    path("logout", views.logout_admin, name="admin_out"),
]

