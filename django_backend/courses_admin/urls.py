from django.urls import path
from . import views

urlpatterns = [
    path("courses_admin", views.courses_admin, name="courses_admin"),
    path("delete_course", views.delete_course, name="delete_course"),
    path("create_course", views.create_course, name="create_course"),
    path("course_exists", views.course_exists, name="course_exists"),
]
