# API URLs for AI Module Integration
from django.urls import path, include
from . import study_plan_views

urlpatterns = [
    # AI plan generate
    path('generate-study-plan/', 
         study_plan_views.GenerateStudyPlanView.as_view(), 
         name='generate_study_plan'),
    
    #generate from db
    path('generate-study-plan-from-db/', 
         study_plan_views.GenerateStudyPlanFromDBView.as_view(), 
         name='generate_study_plan_from_db'),
    
    # ai modulte test
    path('test-ai-module/', 
         study_plan_views.test_ai_module, 
         name='test_ai_module'),
    
    # ai chat api
    path('ai/', include('ai_chat.urls')),
]