from django.urls import path
from . import views

urlpatterns = [
    # 单个任务进度管理
    path("tasks/<int:task_id>/progress", views.task_progress_detail, name="task_progress_detail"),
    
    # 学生所有任务进度
    path("student/progress", views.student_task_progress, name="student_task_progress"),
    
    # 课程下所有任务进度
    path("courses/<str:course_code>/tasks/progress", views.course_tasks_progress, name="course_tasks_progress"),
    path("overdue/report-day", views.overdue_report_day, name="overdue_report_day"),

]