from django.urls import path

from . import views

urlpatterns = [
    path('<str:student_id>/', views.get_reminders, name='get_reminders'),
    path('<int:message_id>/mark-as-read', views.mark_message_as_read),
    path('mark-as-read', views.mark_messages_as_read),
]
