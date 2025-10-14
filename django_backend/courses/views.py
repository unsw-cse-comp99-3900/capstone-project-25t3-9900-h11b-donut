from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.db import models, IntegrityError
from django.conf import settings
from pathlib import Path
from typing import Dict, List
from utils.auth import get_student_id_from_request  # 支持 Bearer Token
from .models import CourseCatalog, CourseTask, StudentEnrollment, TaskProgress, Material

# =====================================
# 保留的页面逻辑（按你要求不删除）
# =====================================

def choose_courses(request):
    # 保留原逻辑；同时兼容 token
    sid = request.session.get("student_id") or get_student_id_from_request(request)
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
        exists = _catalog_exists(code)
        if not exists:
            return render(request, "choose_courses.html", {"message": f"没有查询到该课程：{code}"})

        # 检查是否已选
        if _enrollment_exists(sid, code):
            return redirect(f"/courses/materials/{code}?duplicated=1")

        _enroll_course(sid, code)
        return redirect(f"/courses/materials/{code}?added=1")
    except IntegrityError:
        return render(request, "choose_courses.html", {"message": "选课失败，请稍后再试。"})


def materials_of_course(request, course_code):
    sid = request.session.get("student_id") or get_student_id_from_request(request)
    if sid is None:
        return redirect("index")

    code = (course_code or "").upper()

    # 查询资料（如果存表则从 DB，当前用内存/目录）
    materials = _get_materials_for_course(code)

    added = request.GET.get("added")
    duplicated = request.GET.get("duplicated")

    return render(request, "materials.html", {
        "code": code,
        "materials": materials,
        "added": added,
        "duplicated": duplicated
    })


def show_my_material(request, course_code):
    sid = request.session.get("student_id") or get_student_id_from_request(request)
    if sid is None:
        return redirect("index")
    code = (course_code or "").upper()
    return render(request, "show_my_material.html", {"code": code})

# =====================================
# JSON APIs（前端调用）
# =====================================

def _require_student(request):
    # 兼容 session 与 Bearer
    sid = request.session.get("student_id") or get_student_id_from_request(request)
    return sid

def search_courses(request):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    q = (request.GET.get("q") or "").strip().lower()
    data = [c for c in COURSE_CATALOG if (q in c["code"].lower() or q in c["title"].lower())] if q else []
    return JsonResponse({"success": True, "data": data})

def available_courses(request):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    return JsonResponse({"success": True, "data": COURSE_CATALOG})

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
    course_id = (payload.get("courseId") or "").strip().upper()
    if not course_id:
        return JsonResponse({"success": False, "message": "courseId required"}, status=400)
    if not _catalog_exists(course_id):
        return JsonResponse({"success": False, "message": "Course not found"}, status=404)

    if _enrollment_exists(sid, course_id):
        return JsonResponse({"success": True, "message": "already enrolled"})

    _enroll_course(sid, course_id)
    return JsonResponse({"success": True})

def my_courses(request):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    codes = ENROLLMENTS_BY_STUDENT.get(sid, set())
    out = [c for c in COURSE_CATALOG if c["code"] in codes]
    return JsonResponse({"success": True, "data": out})

def remove_course(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    code = (course_code or "").upper()
    ENROLLMENTS_BY_STUDENT.get(sid, set()).discard(code)
    return JsonResponse({"success": True})

def course_tasks(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    code = (course_code or "").upper()
    data = [t for t in COURSE_TASKS if t["course_code"] == code]
    return JsonResponse({"success": True, "data": data})

def course_materials(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    code = (course_code or "").upper()
    mats = _get_materials_for_course(code)
    return JsonResponse({"success": True, "data": mats})

def task_progress(request, task_id):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    if request.method == "GET":
        value = PROGRESS_BY_STUDENT_TASK.get((sid, int(task_id)), 0)
        return JsonResponse({"success": True, "data": {"task_id": int(task_id), "progress": value}})

    if request.method == "PUT":
        import json
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            payload = {}
        progress = int(payload.get("progress") or 0)
        progress = max(0, min(100, progress))
        PROGRESS_BY_STUDENT_TASK[(sid, int(task_id))] = progress
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

# =====================================
# 内存模拟数据与辅助方法（Sprint1）
# =====================================

COURSE_CATALOG: List[Dict] = [
    { "code": "COMP9900", "title": "Info Tech Project", "description": "Capstone industry project", "illustration": "admin" },
    { "code": "COMP9417", "title": "Machine Learning", "description": "ML foundations and practice", "illustration": "student" },
    { "code": "COMP6080", "title": "Web Front-End", "description": "Modern web development", "illustration": "orange" },
]

COURSE_TASKS: List[Dict] = [
    { "id": 1, "course_code": "COMP9900", "title": "Project Proposal", "deadline": "2025-12-15", "brief": "Submit initial project proposal", "percent_contribution": 30 },
    { "id": 2, "course_code": "COMP9900", "title": "Mid-term Report", "deadline": "2025-11-20", "brief": "Progress report", "percent_contribution": 40 },
    { "id": 3, "course_code": "COMP9900", "title": "Final Presentation", "deadline": "2025-11-19", "brief": "Presentation and final report", "percent_contribution": 30 },
    { "id": 4, "course_code": "COMP9417", "title": "Assignment 1", "deadline": "2025-11-30", "brief": "Implement linear regression", "percent_contribution": 50 },
    { "id": 5, "course_code": "COMP9417", "title": "Assignment 2", "deadline": "2025-12-20", "brief": "Build a neural network", "percent_contribution": 50 },
]

# 学习材料（前端 api.ts 期望结构）
MATERIALS_BY_COURSE: Dict[str, List[Dict]] = {
    "COMP9900": [
        {
            "id": "comp9900-coach-pdf",
            "title": "Capstone Guide",
            "fileType": "pdf",
            "fileSize": "1.2MB",
            "description": "Project guidance document",
            "uploadDate": "2025-10-01"
        }
    ],
    "COMP9417": [],
    "COMP6080": []
}

# 学生选课与任务进度（内存）
ENROLLMENTS_BY_STUDENT: Dict[str, set] = {}
PROGRESS_BY_STUDENT_TASK: Dict[tuple, int] = {}  # key: (student_id, task_id)

def _catalog_exists(code: str) -> bool:
    return any(c["code"] == code for c in COURSE_CATALOG)

def _enrollment_exists(student_id: str, code: str) -> bool:
    return code in ENROLLMENTS_BY_STUDENT.get(student_id, set())

def _enroll_course(student_id: str, code: str):
    ENROLLMENTS_BY_STUDENT.setdefault(student_id, set()).add(code)

def _get_materials_for_course(code: str) -> List[Dict]:
    return MATERIALS_BY_COURSE.get(code, [])

# =====================================
# 路由在 urls.py 中应映射如下：
# path("courses/available", available_courses)
# path("courses/search", search_courses)
# path("courses/add", add_course)
# path("courses/my", my_courses)
# path("courses/<str:course_code>", materials_of_course)  # 保留页面
# path("courses/<str:course_code>/materials", course_materials)  # JSON
# path("courses/<str:course_code>/tasks", course_tasks)
# path("courses/<str:course_code>/remove", remove_course)  # 或 DELETE /courses/{code}
# path("materials/<str:material_id>/download", download_material)
# path("tasks/<int:task_id>/progress", task_progress)