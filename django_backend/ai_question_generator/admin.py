from django.contrib import admin
from .models import GeneratedQuestion, StudentAnswer


@admin.register(GeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'course_code', 'topic', 'question_type', 'created_at']
    list_filter = ['question_type', 'course_code']
    search_fields = ['session_id', 'topic', 'course_code']
    readonly_fields = ['created_at']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'student_id', 'question', 'submitted_at', 'graded_at']
    list_filter = ['submitted_at', 'graded_at']
    search_fields = ['session_id', 'student_id']
    readonly_fields = ['submitted_at', 'graded_at']
