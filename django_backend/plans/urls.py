from django.urls import path
from .views import weekly_plan
from . import views


urlpatterns = [
    path('plans/weekly/<int:week_offset>', weekly_plan),
    path("generate", views.generate_ai_plan, name="generate_ai_plan"),
    path("save", views.save_weekly_plans, name="save_weekly_plans"),
    path('weekly/all', views.get_all_weekly_plans, name='get_all_weekly_plans'),
    path("ai-details", views.get_ai_plan_details, name="get_ai_plan_details"),
]