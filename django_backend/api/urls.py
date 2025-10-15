# API URLs for AI Module Integration
from django.urls import path
from . import study_plan_views

urlpatterns = [
    # AI学习计划生成API
    path('generate-study-plan/', 
         study_plan_views.GenerateStudyPlanView.as_view(), 
         name='generate_study_plan'),
    
    # 从数据库生成学习计划API
    path('generate-study-plan-from-db/', 
         study_plan_views.GenerateStudyPlanFromDBView.as_view(), 
         name='generate_study_plan_from_db'),
    
    # 测试AI模块API
    path('test-ai-module/', 
         study_plan_views.test_ai_module, 
         name='test_ai_module'),
]