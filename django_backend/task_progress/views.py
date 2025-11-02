import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import TaskProgress
from stu_accounts.models import StudentAccount


def _require_student(request):
    """从请求中提取学生ID（支持 Bearer token，与 courses/_require_student 一致）"""
    # 优先解析 Authorization: Bearer <token>
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
    
    # 回退到 Django 用户
    if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
        return getattr(request.user, 'username', None)
    
    # 回退到自定义头或 session
    student_id = request.headers.get('X-Student-ID')
    if student_id:
        return student_id
    return request.session.get('student_id')

@csrf_exempt
@require_http_methods(["GET", "PUT"])
def task_progress_detail(request, task_id):
    """获取或更新特定任务的进度"""
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    if request.method == "GET":
        # 获取任务进度
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
        # 更新任务进度
        try:
            payload = json.loads(request.body.decode("utf-8"))
            progress = int(payload.get("progress") or 0)
            progress = max(0, min(100, progress))  # 确保进度在0-100之间
            
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
    """获取学生所有任务的进度"""
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # 获取该学生的所有任务进度
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
    """获取学生特定课程下所有任务的进度"""
    sid = _require_student(request)
    if sid is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # 需要导入CourseTask模型来获取课程的任务列表
        from courses.models import CourseTask
        
        # 获取课程的所有任务
        course_tasks = CourseTask.objects.filter(course_code=course_code)
        task_ids = [task.id for task in course_tasks]
        
        # 获取这些任务的进度
        progress_list = TaskProgress.objects.filter(
            student_id=sid, 
            task_id__in=task_ids
        )
        
        # 构建进度映射
        progress_map = {progress.task_id: progress.progress for progress in progress_list}
        
        # 返回所有任务的进度（包括进度为0的任务）
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
        # 如果courses应用不可用，返回空列表
        return JsonResponse({"success": True, "data": []})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)