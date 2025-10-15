import json
from datetime import datetime, timedelta
from typing import Dict, List
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from utils.auth import get_student_id_from_request
#from courses.views import MY_COURSES_BY_STUDENT, TASKS_BY_COURSE, _course_color

from ai_module.plan_generator import generate_plan
from accounts.models import StudentAccount
from preferences.models import StudentPreference, StudentPreferenceDefault
from courses.models import StudentEnrollment, CourseTask
from decimal import Decimal

def _auth(request: HttpRequest):
    sid = get_student_id_from_request(request)
    if not sid:
        return None
    return sid

def _ok(data=None):
    return JsonResponse({"success": True, "data": data})

def _err(msg, status=400):
    return JsonResponse({"success": False, "message": msg}, status=status)

# 原型计划存储（每学生、每周偏移）：
PLANS_BY_STUDENT: Dict[str, Dict[int, List[Dict]]] = {}

def _current_monday(offset: int) -> datetime:
    now = datetime.now()
    # Python weekday(): Monday=0 .. Sunday=6
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    monday = monday + timedelta(days=offset*7)
    return monday

def _gen_parts_for_task(course_id: str, task: Dict) -> List[Dict]:
    # 简化的拆分策略：固定生成 3 个部分，总计 ~90min
    titles = ["Part 1 - Preparation", "Part 2 - Execution", "Part 3 - Review"]
    minutes = [30, 40, 20]
    parts = []
    for idx, (tt, mm) in enumerate(zip(titles, minutes), start=1):
        parts.append({
            "id": f"{course_id}-{task['id']}",  # 与前端期望的任务ID层级对齐
            "courseId": course_id,
            "courseTitle": f"{course_id} - {task['title']}",
            "partTitle": tt,
            "minutes": mm,
            "color": _course_color(course_id),
            "completed": False,
            "partIndex": idx,
            "partsCount": len(titles),
        })
    return parts

@csrf_exempt
def weekly_plan(request: HttpRequest, week_offset: int):
    sid = _auth(request)
    if not sid:
        return _err("Unauthorized", 401)

    if request.method == "GET":
        # 若已有生成的计划，则直接返回
        existing = PLANS_BY_STUDENT.get(sid, {}).get(week_offset)
        if existing is not None:
            return _ok(existing)

        # 假设 plan 已经生成：为当前学生的“我的课程”生成 parts 并分布到当前周
        my_course_ids = MY_COURSES_BY_STUDENT.get(sid, [])
        if not my_course_ids:
            return _ok([])

        monday = _current_monday(week_offset)
        # 简单按顺序把 parts 填充到 Mon..Sun
        day_ptr = 0
        items: List[Dict] = []
        for cid in my_course_ids:
            tasks = TASKS_BY_COURSE.get(cid, [])
            for t in tasks:
                for part in _gen_parts_for_task(cid, t):
                    date = monday + timedelta(days=day_ptr % 7)
                    items.append({**part, "date": date.strftime("%Y-%m-%d")})
                    day_ptr += 1

        # 缓存
        PLANS_BY_STUDENT.setdefault(sid, {})[week_offset] = items
        return _ok(items)

    if request.method == "PUT":
        # 保存（覆盖）该周计划
        try:
            body = json.loads((request.body or b"").decode("utf-8") or "{}")
            plan = body.get("plan") or []
            if not isinstance(plan, list):
                return _err("Invalid plan payload", 400)
        except Exception:
            return _err("Invalid JSON", 400)

        PLANS_BY_STUDENT.setdefault(sid, {})[week_offset] = plan
        return _ok()

    return _err("Method Not Allowed", 405)




@csrf_exempt
def generate_ai_plan(request):
    """AI 计划生成调试接口：整合 courses + preferences + AI"""
    # sid = get_student_id_from_request(request)
    # if not sid:
    #     return JsonResponse({"success": False, "message": "Unauthorized"}, status=401)
    sid = "z5540730" 

    # 1️⃣ 获取当前学生对象
    try:
        student = StudentAccount.objects.get(student_id=sid)
    except StudentAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Student not found"}, status=404)
    
    # 2️⃣ 读取学生偏好（优先使用 default 表，没有则用 current 表）
    pref = StudentPreferenceDefault.objects.filter(student=student).first()
    if not pref:
        pref = StudentPreference.objects.filter(student=student).first()

    # 解析偏好数据（如果学生没设置就用默认值）
    if pref:
        preferences = {
            "daily_hour_cap": float(pref.daily_hours or Decimal("3")),
            "weekly_study_days": int(pref.weekly_study_days or 5),
            "avoid_days": [],
        }

        # bitmask 转数组，例如二进制 1100000 -> [5,6] (表示避开周六周日)
        mask = int(pref.avoid_days_bitmask or 0)
        for i in range(7):  # 0=Sun, 6=Sat
            if mask & (1 << i):
                preferences["avoid_days"].append(i)
    else:
        # 如果数据库里啥都没设置，给个默认偏好
        preferences = {"daily_hour_cap": 3, "weekly_study_days": 5, "avoid_days": [5, 6]}

    # 3️⃣ 获取学生选的所有课程及任务
    from courses.models import StudentEnrollment, CourseTask

    # 找出该学生选了哪些课程
    enrolled_courses = StudentEnrollment.objects.filter(student_id=sid).values_list("course_code", flat=True)

    tasks_meta = []
    for course_code in enrolled_courses:
        # 查该课程下的任务
        tasks = CourseTask.objects.filter(course_code=course_code).values(
            "id", "title", "deadline", "brief"
        )

        for t in tasks:
            # 转成 AI 模块所需的格式
            task_meta = {
                "id": f"{course_code}_{t['id']}",
                "task": f"{course_code} - {t['title']}",
                "dueDate": t["deadline"].isoformat() if t["deadline"] else None,
                "detailPdfPath": None,  # 暂时没有 PDF 文件路径，可后续添加
                "estimatedHours": 3     # 临时估计 3 小时，AI 模块会自动修正
            }
            tasks_meta.append(task_meta)

    if not tasks_meta:
        return JsonResponse({"success": False, "message": "No tasks found"}, status=404)
    
    # 4️⃣ 调用 AI 模块生成学习计划
    from ai_module.plan_generator import generate_plan

    try:
        ai_result = generate_plan(preferences, tasks_meta)

        # 直接返回结果
        return JsonResponse(ai_result, safe=False)

    except Exception as e:
        print("[AI_GENERATE_PLAN_ERROR]", str(e))
        return JsonResponse({
            "success": False,
            "message": f"AI Plan generation failed: {str(e)}"
        }, status=500)




