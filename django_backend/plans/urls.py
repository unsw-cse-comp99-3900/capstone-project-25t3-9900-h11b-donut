from django.urls import path
from .views import weekly_plan

urlpatterns = [
    path('plans/weekly/<int:week_offset>', weekly_plan),
]