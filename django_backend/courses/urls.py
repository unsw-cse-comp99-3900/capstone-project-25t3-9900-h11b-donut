from django.urls import path
from . import views

urlpatterns = [
    # 页面（保留）
    path("courses/choose", views.choose_courses),
    path("courses/<str:course_code>/materials-page", views.materials_of_course),
    path("courses/<str:course_code>/show", views.show_my_material),

    # JSON APIs（/api 前缀由 project/urls.py include 时加上）
    path("courses/available", views.available_courses),
    path("courses/search", views.search_courses),
    path("courses/add", views.add_course),
    path("courses/my", views.my_courses),
    path("courses/<str:course_code>/materials", views.course_materials),
    path("courses/<str:course_code>/tasks", views.course_tasks),
    path("courses/<str:course_code>", views.remove_course),  # DELETE
    path("materials/<str:material_id>/download", views.download_material),
]