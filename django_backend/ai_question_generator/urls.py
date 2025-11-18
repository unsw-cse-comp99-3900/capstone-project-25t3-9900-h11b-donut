"""
AI Question Generator URLs
"""
from django.urls import path
from . import views

app_name = 'ai_question_generator'

urlpatterns = [
    # 示例题目管理
    path('sample-questions/upload', views.upload_sample_questions, name='upload_sample_questions'),
    path('sample-questions', views.get_sample_questions, name='get_sample_questions'),
    
    # AI题目生成
    path('questions/generate', views.generate_questions, name='generate_questions'),
    path('questions/session/<str:session_id>', views.get_session_questions, name='get_session_questions'),
    
    # 学生答题与评分
    path('answers/submit', views.submit_answers, name='submit_answers'),
    path('results', views.get_student_results, name='get_student_results'),
]
