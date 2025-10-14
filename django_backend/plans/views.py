import json
from datetime import datetime, timedelta
from typing import Dict, List
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from utils.auth import get_student_id_from_request
from courses.views import MY_COURSES_BY_STUDENT, TASKS_BY_COURSE, _course_color

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