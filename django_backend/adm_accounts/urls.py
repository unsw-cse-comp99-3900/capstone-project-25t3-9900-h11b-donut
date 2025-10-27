from django.urls import path
from . import views

urlpatterns = [
    path("register", views.register_admin, name="admin_register"),
]

