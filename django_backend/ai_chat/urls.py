from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    # 对话相关API
    path('chat/', views.ChatView.as_view(), name='chat'),
    
    # 学习计划存储API
    path('study-plan/', views.StudyPlanView.as_view(), name='study_plan'),
    
    # 数据清理API
    path('cleanup/', views.CleanupView.as_view(), name='cleanup'),
    
    # 问候检查API
    path('greeting-check/', views.GreetingCheckView.as_view(), name='greeting_check'),
    
    # 健康检查API
    path('health/', views.HealthCheckView.as_view(), name='health'),
]