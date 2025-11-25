from django.urls import path
from . import views

urlpatterns = [
    
    path("tasks/<int:task_id>/progress", views.task_progress_detail, name="task_progress_detail"),
    
   
    path("student/progress", views.student_task_progress, name="student_task_progress"),
    
 
    path("courses/<str:course_code>/tasks/progress", views.course_tasks_progress, name="course_tasks_progress"),
    path("overdue/report-day", views.overdue_report_day, name="overdue_report_day"),

]