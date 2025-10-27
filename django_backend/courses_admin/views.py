import logging
import json
from django.http import JsonResponse
from .models import CourseAdmin  # 假设你的表名是 courses_admin
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from courses.models import CourseCatalog,StudentEnrollment,TaskProgress,CourseTask
from django.db import transaction,IntegrityError
from django.shortcuts import get_object_or_404
logger = logging.getLogger(__name__)
def courses_admin(request):
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)


    admin_id = request.GET.get('admin_id')
    if not admin_id:
        return JsonResponse({"success": True, "data": []})

    rows = CourseAdmin.objects.filter(admin_id=admin_id).values('admin_id', 'code')
    data = list(rows)
    codes = [row['code'] for row in data]
    if not codes:
        return JsonResponse({"success": True, "data": []})
    
    course_map = {
        c['code']: c
        for c in CourseCatalog.objects.filter(code__in=codes).values('code', 'title', 'description','illustration')
    }
    enroll_counts_qs = (
        StudentEnrollment.objects
        .filter(course_code__in=codes)
        .values('course_code')
        .annotate(n=Count('student_id', distinct=True))
    )
    enroll_count_map = {row['course_code']: row['n'] for row in enroll_counts_qs}
    enriched = []
    enriched = []
    for row in data:
        code = row['code']
        c = course_map.get(code, {})
        enriched.append({
            "code": code,
            "title": c.get("title", ""),
            "description": c.get("description", ""),
            "illustration": c.get("illustration", ""),
            "student_count": enroll_count_map.get(code, 0),  # 新增：该课程的学生人数
        })
    
    return JsonResponse({"success": True, "data": enriched})
@csrf_exempt
def course_exists(request):
    code = (request.GET.get("code") or "").strip().upper()
    if not code:
        return JsonResponse({"success": False, "message": "missing code"}, status=400)
    exists = CourseCatalog.objects.filter(code=code).exists()
    return JsonResponse({
    "success": True,
    "data": { "exists": exists }
})
@csrf_exempt
def create_course(request):
    # 1) 取参（form > json > query）
    admin_id = request.POST.get("admin_id") or request.GET.get("admin_id")
    code = request.POST.get("code") or request.GET.get("code")
    title = request.POST.get("title") or request.GET.get("title")
    description = request.POST.get("description") or request.GET.get("description") or ""
    # illustration 可选：如果你的 CourseCatalog 有这个字段就用；没有就忽略
    illustration = request.POST.get("illustration") or request.GET.get("illustration")

    if (not admin_id or not code or not title) and request.body:
        try:
            data = json.loads(request.body.decode("utf-8"))
            admin_id = admin_id or data.get("admin_id")
            code = code or data.get("code")
            title = title or data.get("title")
            description = description or data.get("description") or ""
            illustration = illustration or data.get("illustration")
        except Exception:
            pass

    code = (code or "").strip().upper()
    title = (title or "").strip()
    description = (description or "").strip()

    if not admin_id or not code or not title:
        return JsonResponse({"success": False, "message": "缺少参数：admin_id / code / title"}, status=400)

    # 2) 事务内创建或更新课程 + 关联管理员
    try:
        with transaction.atomic():
            # 2.1 创建或更新课程（幂等）
            defaults = {"title": title, "description": description}
            # 仅当模型真的有 illustration 字段时才写入，避免 AttributeError
            if illustration is not None and hasattr(CourseCatalog, "_meta") and any(
                f.name == "illustration" for f in CourseCatalog._meta.fields
            ):
                defaults["illustration"] = illustration

            course, created = CourseCatalog.objects.get_or_create(code=code, defaults=defaults)
            if not created:
                # 更新基础信息（只更新传入的字段）
                course.title = title
                course.description = description
                if illustration is not None and hasattr(CourseCatalog, "_meta") and any(
                    f.name == "illustration" for f in CourseCatalog._meta.fields
                ):
                    setattr(course, "illustration", illustration)
                course.save()

            # 2.2 建立管理员与课程的关联（外键字段名是 code）
            CourseAdmin.objects.get_or_create(admin_id=admin_id, code=course)

        return JsonResponse({
            "success": True,
            "message": f"课程 {code} 已{'创建' if created else '更新'}",
            "created": created
        })

    except IntegrityError as e:
        return JsonResponse({"success": False, "message": f"创建失败：{e}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"系统错误：{e}"}, status=500)
@csrf_exempt
def delete_course(request):
    """
    删除课程及其所有关联数据,联级别删除！！！
    """
    # 1) 取参
    admin_id = request.POST.get("admin_id") or request.GET.get("admin_id")
    code = request.POST.get("code") or request.GET.get("code")

    if (not admin_id or not code) and request.body:
        try:
            data = json.loads(request.body.decode("utf-8"))
            admin_id = admin_id or data.get("admin_id")
            code = code or data.get("code")
        except Exception:
            pass

    if not admin_id or not code:
        return JsonResponse({"success": False, "message": "wrong!"}, status=400)

    # 2) 基本对象与权限
    course = get_object_or_404(CourseCatalog, code=code)

    if not CourseAdmin.objects.filter(admin_id=admin_id, code__code=code).exists():
        return JsonResponse({"success": False, "message": "wrong!"}, status=403)

    # 3) （TaskProgress -> CourseTask -> CourseAdmin -> CourseCatalog）
    try:
        with transaction.atomic():
            # 找到所有任务 id
            task_ids = list(
                CourseTask.objects.filter(course_code=code).values_list("id", flat=True)
            )
            # 先删进度
            if task_ids:
                TaskProgress.objects.filter(task_id__in=task_ids).delete()
            # 再删任务
            CourseTask.objects.filter(course_code=code).delete()
            # 删管理员关联
            CourseAdmin.objects.filter(admin_id=admin_id, code__code=code).delete()
            # 最后删课程
            course.delete()

        return JsonResponse({"success": True, "message": f"课程 {code} 已成功删除"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"删除失败：{e}"}, status=500)