
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_id', 'course_code', 'message_type', 'title', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'course_code')
    search_fields = ('student_id', 'title', 'preview', 'content')
