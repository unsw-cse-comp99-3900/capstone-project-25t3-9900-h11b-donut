import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import TaskProgress
from stu_accounts.models import StudentAccount
from .models import (
    OverdueStudent,
    OverdueCourseStudent,
    OverdueStudentDailyLog,
    OverdueTaskDailyLog,
)
from typing import Dict, List, Tuple
from django.db import IntegrityError, transaction, models
from django.utils import timezone
from datetime import date, datetime
from typing import Any, Dict, List

def _require_student(request):
    """get stu ID from request"""
    # decode Authorization: Bearer <token>
    auth = request.headers.get("Authorization", "") or request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        sid = (
            StudentAccount.objects
            .filter(current_token=token)
            .values_list("student_id", flat=True)
            .first()
        )
        if sid:
            return sid
    
    # back to  Django user
    if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
        return getattr(request.user, 'username', None)
    #back to session
    student_id = request.headers.get('X-Student-ID')
    if student_id:
        return student_id
    return request.session.get('student_id')

@csrf_exempt
@require_http_methods(["GET", "PUT"])
def task_progress_detail(request, task_id):
    """get specific task's progress"""
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    if request.method == "GET":
        try:
            row = TaskProgress.objects.filter(student_id=sid, task_id=int(task_id)).first()
            value = row.progress if row else 0
            return JsonResponse({
                "success": True, 
                "data": {
                    "task_id": int(task_id), 
                    "progress": value,
                    "student_id": sid
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    elif request.method == "PUT":
        # update the progress bar
        try:
            payload = json.loads(request.body.decode("utf-8"))
            progress = int(payload.get("progress") or 0)
            progress = max(0, min(100, progress))  # progress between 0-100
            
            TaskProgress.objects.update_or_create(
                student_id=sid,
                task_id=int(task_id),
                defaults={"progress": progress}
            )
            return JsonResponse({"success": True})
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({"success": False, "error": "Invalid progress value"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def student_task_progress(request):
    """stu progress"""
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # all tasks of this stu
        progress_list = TaskProgress.objects.filter(student_id=sid)
        data = [
            {
                "task_id": progress.task_id,
                "progress": progress.progress,
                "updated_at": progress.updated_at.isoformat() if progress.updated_at else None
            }
            for progress in progress_list
        ]
        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def course_tasks_progress(request, course_code):
    """get stu's courses with all tasks"""
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # get the table 
        from courses.models import CourseTask
        
        # get all tasks
        course_tasks = CourseTask.objects.filter(course_code=course_code)
        task_ids = [task.id for task in course_tasks]
        
        # get all progress
        progress_list = TaskProgress.objects.filter(
            student_id=sid, 
            task_id__in=task_ids
        )
        
        # progress projection
        progress_map = {progress.task_id: progress.progress for progress in progress_list}
        
        # get all progress 0~100
        data = []
        for task in course_tasks:
            progress = progress_map.get(task.id, 0)
            data.append({
                "task_id": task.id,
                "task_title": task.title,
                "progress": progress,
                "deadline": task.deadline.isoformat() if task.deadline else None
            })
        
        return JsonResponse({"success": True, "data": data})
    except ImportError:
        # no course, return empty list
        return JsonResponse({"success": True, "data": []})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def overdue_report_day(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)


    student_id = payload.get("student_id")
    date_str = payload.get("date")  # 期望: YYYY-MM-DD
    overdue_tasks = payload.get("overdue_tasks", [])  # [{course_code, task_id}, ...]
    is_whole_day_overdue = payload.get("is_whole_day_overdue", False)


    if not isinstance(student_id, str) or not student_id:
        return JsonResponse({"ok": False, "error": "student_id required"}, status=400)

    if not isinstance(date_str, str) or len(date_str) != 10:
        return JsonResponse({"ok": False, "error": "date must be YYYY-MM-DD"}, status=400)

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"ok": False, "error": "invalid date format"}, status=400)

    if not isinstance(overdue_tasks, list):
        return JsonResponse({"ok": False, "error": "overdue_tasks must be a list"}, status=400)


    normalized_tasks: List[Dict[str, str]] = []
    for i, t in enumerate(overdue_tasks):
        if not isinstance(t, dict):
            return JsonResponse({"ok": False, "error": f"overdue_tasks[{i}] must be an object"}, status=400)
        cc = t.get("course_code")
        tid = t.get("task_id")
        if not (isinstance(cc, str) and cc) or not (isinstance(tid, str) and tid):
            return JsonResponse(
                {"ok": False, "error": f"overdue_tasks[{i}] needs course_code(str) & task_id(str)"},
                status=400,
            )
        normalized_tasks.append({"course_code": cc, "task_id": tid})

    if not isinstance(is_whole_day_overdue, bool):
        return JsonResponse({"ok": False, "error": "is_whole_day_overdue must be boolean"}, status=400)


    student_overdue_incremented = False
    task_overdue_incremented_count = 0


    if is_whole_day_overdue:
        try:
            with transaction.atomic():
                log, created = OverdueStudentDailyLog.objects.get_or_create(
                    student_id=student_id,
                    date=day,
                    defaults={"reason": ""},
                )
                if created:
                    stu, _ = OverdueStudent.objects.get_or_create(student_id=student_id)
                    stu.count_overdue = (stu.count_overdue or 0) + 1
                    stu.save(update_fields=["count_overdue", "updated_at"])
                    student_overdue_incremented = True
        except IntegrityError:

            pass


    seen = set()
    for item in normalized_tasks:
        key = (student_id, item["course_code"], item["task_id"], day)
        if key in seen:
            continue
        seen.add(key)

        try:
            with transaction.atomic():
                tlog, created = OverdueTaskDailyLog.objects.get_or_create(
                    student_id=student_id,
                    course_code=item["course_code"],
                    task_id=item["task_id"],
                    date=day,
                )
                if created:
                    ocs, _ = OverdueCourseStudent.objects.get_or_create(
                        student_id=student_id,
                        course_code=item["course_code"],
                        task_id=item["task_id"],
                    )
                    ocs.count_overdue = (ocs.count_overdue or 0) + 1
                    ocs.save(update_fields=["count_overdue", "updated_at"])
                    task_overdue_incremented_count += 1
        except IntegrityError:
            # same log ,skip
            pass

    # ---------- return ----------
    return JsonResponse(
        {
            "ok": True,
            "received": {
                "student_id": student_id,
                "date": date_str,
                "overdue_tasks_count": len(normalized_tasks),
                "is_whole_day_overdue": is_whole_day_overdue,
            },
            "updates": {
                "student_overdue_incremented": student_overdue_incremented,
                "task_overdue_incremented_count": task_overdue_incremented_count,
            },
        },
        status=200,
    )
