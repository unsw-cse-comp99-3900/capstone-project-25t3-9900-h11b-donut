from django.urls import path
from . import views

urlpatterns = [
    path("courses_admin", views.courses_admin, name="courses_admin"),
    path("delete_course", views.delete_course, name="delete_course"),
    path("create_course", views.create_course, name="create_course"),
    path("course_exists", views.course_exists, name="course_exists"),
    
    path("courses_admin/<str:course_id>/tasks", views.course_tasks, name="course_tasks"),
    path('courses_admin/<str:course_id>/tasks/create', views.create_course_tasks, name='create_tasks'),
    path('courses_admin/<str:course_id>/tasks/<int:task_id>/delete',views.delete_course_task,name="delete_course_task"),
    path('courses_admin/<str:course_id>/tasks/<int:task_id>', views.update_course_task,name="update_task_question"),
    
    path("courses_admin/<str:course_id>/materials", views.course_materials, name="course_materials"),
    path('courses_admin/<str:course_id>/materials/create', views.create_course_materials, name='create_materials'),
    path('courses_admin/<str:course_id>/materials/<int:materials_id>/delete', views.delete_course_material,name="delete_course_material"),
    path('courses_admin/<str:course_id>/materials/<int:materials>', views.update_course_material,name="update_course_material"),
    
    path("courses_admin/<str:course_id>/questions", views.course_questions, name="course_questions"),
    path("courses_admin/<str:course_code>/questions/create", views.create_course_question, name="create_course_question"),
    path('courses_admin/<str:course_id>/questions/<int:question_id>', views.update_course_question,name="update_course_question"),
    path('courses_admin/<str:course_id>/questions/<int:question_id>/delete', views.delete_course_question,name="delete_course_question"),
    
    path('courses_admin/upload/task-file', views.upload_task_file, name='upload_task_file'),
    path('courses_admin/upload/material-file', views.upload_material_file, name='upload_material_file'),
]