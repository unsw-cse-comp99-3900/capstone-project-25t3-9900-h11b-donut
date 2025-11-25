from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
   
    path('chat/', views.ChatView.as_view(), name='chat'),
    
  
    path('study-plan/', views.StudyPlanView.as_view(), name='study_plan'),
    

    path('cleanup/', views.CleanupView.as_view(), name='cleanup'),
    
  
    path('greeting-check/', views.GreetingCheckView.as_view(), name='greeting_check'),
    

    path('health/', views.HealthCheckView.as_view(), name='health'),
    
  
    path('generate-practice/', views.GeneratePracticeView.as_view(), name='generate_practice'),
]