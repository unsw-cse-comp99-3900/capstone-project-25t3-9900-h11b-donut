"""
AI Question Generator URLs
"""
from django.urls import path
from . import views

app_name = 'ai_question_generator'

urlpatterns = [
    # AI question generating
    path('questions/generate', views.generate_questions, name='generate_questions'),
    path('questions/session/<str:session_id>', views.get_session_questions, name='get_session_questions'),
    
    # Student Answering and Scoring
    path('answers/submit', views.submit_answers, name='submit_answers'),
    path('results', views.get_student_results, name='get_student_results'),
]
