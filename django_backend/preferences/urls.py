# preferences/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.preferences_entry, name='api_preference'),  # /api/preferences
]
