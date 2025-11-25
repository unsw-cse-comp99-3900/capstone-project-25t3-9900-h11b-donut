from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.db import models, IntegrityError,transaction
from django.db.models import Subquery
from django.conf import settings
from pathlib import Path
from typing import Optional
from stu_accounts.models import StudentAccount
from django.views.decorators.csrf import csrf_exempt
from .models import (
    CourseCatalog,
    CourseTask,
    StudentEnrollment,
    Material,
)
from plans.models import StudyPlan,StudyPlanItem
from .models import CourseTask, StudentEnrollment
from task_progress.models import TaskProgress
def choose_courses(request):
    sid = _require_student(request)
   
    if sid is None:
        return redirect("index")

    if request.method == "GET":
        return render(request, "choose_courses.html")

    code = (request.POST.get("course_code") or "").strip().upper()
    if not code:
        return render(request, "choose_courses.html", {"message": "please enter course code"})

    try:
        # check course availablility
        exists = CourseCatalog.objects.filter(code=code).exists()
        if not exists:
            return render(request, "choose_courses.html", {"message": f"no courses found:{code}"})

        # enrolled or not
        if StudentEnrollment.objects.filter(student_id=sid, course_code=code).exists():
            return redirect(f"/courses/materials/{code}?duplicated=1")

        StudentEnrollment.objects.create(student_id=sid, course_code=code)
        return redirect(f"/courses/materials/{code}?added=1")
    except IntegrityError:
        return render(request, "choose_courses.html", {"message": "fail to enroll,try again later"})


def materials_of_course(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return redirect("index")

    code = (course_code or "").upper()

    # get url added / duplicated
    added = request.GET.get("added")
    duplicated = request.GET.get("duplicated")

    # search material
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
    # format mapping 
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

    try:
        with transaction.atomic():
            # delete plan (fair enough cuz u need to regenerate new plan)
            deleted_plans, cascade_details = StudyPlan.objects.filter(
                student_id=sid
            ).delete()
            deleted_plan_items = cascade_details.get(StudyPlanItem._meta.label, 0)
           
            task_ids_subq = CourseTask.objects.filter(
                course_code=code
            ).values('id')

            # 1) delete progress
            deleted_progress_count, _ = TaskProgress.objects.filter(
                student_id=sid,
                task_id__in=Subquery(task_ids_subq)
            ).delete()

            # 2)delete enrollments
            deleted_enroll_count, _ = StudentEnrollment.objects.filter(
                student_id=sid,
                course_code=code
            ).delete()

        return JsonResponse({
            "success": True,
            "deleted": {
                "study_plans": deleted_plans,
                "study_plan_items": deleted_plan_items,
                "task_progress":  deleted_progress_count,
                "student_enrollment": deleted_enroll_count,
            }
        })
    
    except Exception as e:
        return JsonResponse(
            {"error": "Server Error", "detail": repr(e)},
            status=500
        )



from django.utils import timezone

def course_tasks(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)

    code = (course_code or "").upper()

    tasks = CourseTask.objects.filter(course_code=code)

    data = []
    for t in tasks:
        # deadline fits timezone（Australia/Sydney）
        local_deadline = None
        if t.deadline:
            local_deadline = timezone.localtime(t.deadline).strftime("%Y-%m-%d %H:%M:%S")

        data.append({
            "id": t.id,
            "course_code": t.course_code,
            "title": t.title,
            "deadline": local_deadline,   
            "brief": t.brief,
            "percent_contribution": t.percent_contribution,
            "url": t.url,
        })

    return JsonResponse({"success": True, "data": data})

def course_materials(request, course_code):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    code = (course_code or "").upper()
    rows = list(Material.objects.filter(course_code=code).values("title", "url"))
    data = []
    for r in rows:
        url: str = r["url"] or ""
        ext = "pdf"
        if "." in url:
            ext = url.split(".")[-1].lower() or "pdf"
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

def download_material(request, material_id):
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    base = Path(settings.BASE_DIR) / "components"
    file_path = base / f"{material_id}.pdf"
    if not file_path.exists():
        return JsonResponse({"success": False, "message": "Material not found"}, status=404)
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_path.name)

