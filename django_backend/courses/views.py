from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.db import models, IntegrityError
from django.conf import settings
from pathlib import Path
from typing import Optional
from stu_accounts.models import StudentAccount
from django.views.decorators.csrf import csrf_exempt
from .models import (
    CourseCatalog,
    CourseTask,
    StudentEnrollment,
    TaskProgress,
    Material,
)


def choose_courses(request):
    sid = _require_student(request)
   
    if sid is None:
        return redirect("index")

    if request.method == "GET":
        return render(request, "choose_courses.html")

    # POST: 处理新增课程（沿用原来 form 的 course_code）
    code = (request.POST.get("course_code") or "").strip().upper()
    if not code:
        return render(request, "choose_courses.html", {"message": "请输入课程代码。"})

    try:
        # 检查课程是否存在（在 catalog 中）
        exists = CourseCatalog.objects.filter(code=code).exists()
        if not exists:
            return render(request, "choose_courses.html", {"message": f"没有查询到该课程：{code}"})

        # 检查是否已选
        if StudentEnrollment.objects.filter(student_id=sid, course_code=code).exists():
            return redirect(f"/courses/materials/{code}?duplicated=1")

        StudentEnrollment.objects.create(student_id=sid, course_code=code)
        return redirect(f"/courses/materials/{code}?added=1")
    except IntegrityError:
        return render(request, "choose_courses.html", {"message": "选课失败，请稍后再试。"})


def materials_of_course(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return redirect("index")

    code = (course_code or "").upper()

    # 读取 URL 参数 added / duplicated
    added = request.GET.get("added")
    duplicated = request.GET.get("duplicated")

    # 查询资料（从 DB 的 Material)
    mats = Material.objects.filter(course_code=code).values("title", "url")

    return render(request, "materials.html", {
        "code": code,
        "materials": mats,
        "added": added,
        "duplicated": duplicated
    })


def show_my_material(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return redirect("index")
    code = (course_code or "").upper()
    return render(request, "show_my_material.html", {"code": code})

# =========================
# JSON APIs（前端调用）
# =========================

def _require_student(request):
    auth = request.headers.get("Authorization", "") or request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    sid = (
        StudentAccount.objects
        .filter(current_token=token)
        .values_list("student_id", flat=True)
        .first()
    )
    return sid

def available_courses(request):
    sid = _require_student(request)
    
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    rows = list(CourseCatalog.objects.values("code", "title", "description", "illustration"))
    # 映射为前端期望结构（包含 id）
    data = [{"id": r["code"], "title": r["title"], "description": r["description"], "illustration": r["illustration"]} for r in rows]
    return JsonResponse({"success": True, "data": data})

def search_courses(request):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"success": True, "data": []})

    qs = CourseCatalog.objects.filter(
        models.Q(code__icontains=q) | models.Q(title__icontains=q)
    ).values("code", "title", "description", "illustration")
    data = list(qs)
    return JsonResponse({"success": True, "data": data})
@csrf_exempt
def add_course(request):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    import json
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = {}
    code = (payload.get("courseId") or "").strip().upper()
    if not code:
        return JsonResponse({"success": False, "message": "courseId required"}, status=400)
    if not CourseCatalog.objects.filter(code=code).exists():
        return JsonResponse({"success": False, "message": "Course not found"}, status=404)

    _, created = StudentEnrollment.objects.get_or_create(student_id=sid, course_code=code)
    if not created:
        return JsonResponse({"success": True, "message": "already enrolled"})
    return JsonResponse({"success": True})

def my_courses(request):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    codes = list(StudentEnrollment.objects.filter(student_id=sid).values_list("course_code", flat=True))
    rows = list(CourseCatalog.objects.filter(code__in=codes).values("code", "title", "description", "illustration"))
    data = [{"id": r["code"], "title": r["title"], "description": r["description"], "illustration": r["illustration"]} for r in rows]
    return JsonResponse({"success": True, "data": data})
@csrf_exempt
def remove_course(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    code = (course_code or "").upper()
    StudentEnrollment.objects.filter(student_id=sid, course_code=code).delete()
    return JsonResponse({"success": True})

def course_tasks(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    code = (course_code or "").upper()
    qs = CourseTask.objects.filter(course_code=code).values(
        "id", "course_code", "title", "deadline", "brief", "percent_contribution"
    )
    data = list(qs)
    return JsonResponse({"success": True, "data": data})

def course_materials(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    code = (course_code or "").upper()
    rows = list(Material.objects.filter(course_code=code).values("title", "url"))
    # 视图层补齐前端期望的字段结构
    data = []
    for r in rows:
        url: str = r["url"] or ""
        # 推断 fileType：扩展名或默认 pdf
        ext = "pdf"
        if "." in url:
            ext = url.split(".")[-1].lower() or "pdf"
        # 生成 id：优先根据文件名，无则基于标题派生
        base_name = url.split("/")[-1] if "/" in url else url
        base_name = base_name.split(".")[0] if "." in base_name else base_name
        mat_id = base_name or r["title"].lower().replace(" ", "-")
        data.append({
            "id": mat_id,
            "title": r["title"],
            "fileType": ext,
            "fileSize": "unknown",
            "description": "Course material",
            "uploadDate": "unknown",
        })
    return JsonResponse({"success": True, "data": data})
@csrf_exempt
def task_progress(request, task_id):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    if request.method == "GET":
        row = TaskProgress.objects.filter(student_id=sid, task_id=int(task_id)).first()
        value = row.progress if row else 0
        return JsonResponse({"success": True, "data": {"task_id": int(task_id), "progress": value}})

    if request.method == "PUT":
        import json
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            payload = {}
        progress = int(payload.get("progress") or 0)
        progress = max(0, min(100, progress))
        TaskProgress.objects.update_or_create(
            student_id=sid,
            task_id=int(task_id),
            defaults={"progress": progress}
        )
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Method not allowed"}, status=405)

def download_material(request, material_id):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    # material_id → 组件目录文件名
    base = Path(settings.BASE_DIR) / "components"
    file_path = base / f"{material_id}.pdf"
    if not file_path.exists():
        return JsonResponse({"success": False, "message": "Material not found"}, status=404)
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_path.name)

# =========================
# 路由在 urls.py 中应映射如下（示例）
# path("courses/available", available_courses)
# path("courses/search", search_courses)
# path("courses/add", add_course)
# path("courses/my", my_courses)
# path("courses/<str:course_code>/materials", course_materials)
# path("courses/<str:course_code>/tasks", course_tasks)
# path("courses/<str:course_code>", remove_course)  # DELETE /courses/{code}
# path("materials/<str:material_id>/download", download_material)
# path("tasks/<int:task_id>/progress", task_progress)
# =========================