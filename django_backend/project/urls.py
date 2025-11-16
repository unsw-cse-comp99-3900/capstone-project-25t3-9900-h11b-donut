"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('courses_admin.urls')),
    path('api/preferences', include('preferences.urls')),
    path('api/', include('stu_accounts.urls')),
    path('api/', include('courses.urls')),
    path('api/', include('api.urls')),
    path('api/', include('plans.urls')),
    path("api/admin/", include("adm_accounts.urls")),
    path("api/", include("task_progress.urls")),
    path('api/reminders/', include('reminder.urls')),
    path('api/ai/', include('ai_question_generator.urls')),  # AI题目生成与评分

] 
if settings.DEBUG:
    # 已有的 /media/ 映射
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # 新增 /api/media/ 映射，用于兼容前端拼了 /api 的情况(用于登录头像)
    urlpatterns += static('/api/media/', document_root=settings.MEDIA_ROOT)
    # 映射task 可选：兼容前端拼了 /api/task/ 的情况
    urlpatterns += static(settings.TASK_URL, document_root=settings.TASK_ROOT)
    urlpatterns += static('/api/task/', document_root=settings.TASK_ROOT)
    urlpatterns += static(settings.MAT_URL, document_root=settings.MAT_ROOT)
    # 可选：兼容前端带 /api 前缀的情况
    urlpatterns += static('/api/material/', document_root=settings.MAT_ROOT)