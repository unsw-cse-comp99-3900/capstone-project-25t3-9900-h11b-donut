from django.urls import path
from . import views

urlpatterns = [
    path('choose', views.choose_courses, name='choose_courses'),
    path('materials/<str:course_code>', views.materials_of_course, name='materials_of_course'),
    path('show_my_material/<str:course_code>', views.show_my_material, name='show_my_material'),
]
