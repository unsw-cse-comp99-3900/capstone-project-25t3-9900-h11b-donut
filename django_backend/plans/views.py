import json
from datetime import datetime, timedelta,date
from typing import Dict, List
from django.utils import timezone
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from utils.auth import get_student_id_from_request
from typing import Optional
from ai_module.plan_generator import generate_plan
from stu_accounts.models import StudentAccount
from preferences.models import StudentPreference, StudentPreferenceDefault
from courses.models import StudentEnrollment, CourseTask
from decimal import Decimal
from ai_module.plan_generator import generate_plan
from .models import StudyPlan, StudyPlanItem
from django.db import transaction
from django.db.models import Prefetch
def _auth(request: HttpRequest) -> Optional[str]:
    """
    返回当前已登录学生ID。
    优先使用 session，再尝试从 Authorization: Bearer <token> 中查数据库。
    """
    sid = request.session.get("student_id")
    if sid:
        return sid

    auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
    if not auth.startswith("Bearer "):
        return None

    token = auth[7:].strip()
    if not token:
        return None

    account = (
        StudentAccount.objects
        .only("student_id")
        .filter(current_token=token)
        .first()
    )
    return account.student_id if account else None

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
    print(f"🚀 [GENERATE_AI_PLAN] 收到请求: {request.method}")
    print(f"🚀 [GENERATE_AI_PLAN] Headers: {dict(request.headers)}")
    
    sid = get_student_id_from_request(request)
    print(f"🚀 [GENERATE_AI_PLAN] 学生ID: {sid}")
    
    if not sid:
        print("❌ [GENERATE_AI_PLAN] 未授权访问")
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=401)
    # 1️⃣ 获取当前学生对象
    try:
        student = StudentAccount.objects.get(student_id=sid)
    except StudentAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Student not found"}, status=404)
    
    # 2️⃣ 读取学生偏好（优先使用 current 表，没有则用 default 表）
    pref = StudentPreference.objects.filter(student=student).first()
    pref_source = "current"
    if not pref:
        pref = StudentPreferenceDefault.objects.filter(student=student).first()
        pref_source = "default"
    
    print(f"📋 [GENERATE_AI_PLAN] 偏好来源: {pref_source}")
    if pref:
        print(f"📋 [GENERATE_AI_PLAN] 原始偏好数据: daily_hours={pref.daily_hours}, weekly_study_days={pref.weekly_study_days}, avoid_days_bitmask={pref.avoid_days_bitmask}")
    else:
        print(f"📋 [GENERATE_AI_PLAN] 未找到偏好数据，将使用默认值")
    

    # 解析偏好数据（如果学生没设置就用默认值）
    if pref:
        WEEK_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        preferences = {
            "dailyHours": float(pref.daily_hours or 4),  # 默认4小时，不是0
            "weeklyStudyDays": int(pref.weekly_study_days or 5),
            "avoidDays": [],
        }
        
    
        # bitmask 转数组，例如二进制 1100000 -> [5,6] (表示避开周六周日)
        mask = int(pref.avoid_days_bitmask or 0)
        for i in range(7):  # 0=Sun, 6=Sat
            if mask & (1 << i):
                preferences["avoidDays"].append(WEEK_LABELS[i])
    else:
        # 如果数据库里啥都没设置，给个默认偏好
        preferences = {
        "dailyHours": 4,  # 默认4小时，与前端一致
        "weeklyStudyDays": 5,  # 默认5天，与前端一致
        "avoidDays": ["Sun", "Sat"],  # 默认避开周末
    }
    print(f"📋 [GENERATE_AI_PLAN] 最终偏好数据: {preferences}")
    print(f"📋 [GENERATE_AI_PLAN] 偏好来源: {pref_source if 'pref_source' in locals() else 'unknown'}")

    # 3️⃣ 获取学生选的所有课程及任务
    from courses.models import StudentEnrollment, CourseTask

    # 找出该学生选了哪些课程
    enrolled_courses = StudentEnrollment.objects.filter(student_id=sid).values_list("course_code", flat=True)
    
    tasks_meta = []
    for course_code in enrolled_courses:
        # 查该课程下的任务
        tasks = CourseTask.objects.filter(course_code=course_code).values(
            "id", "title", "deadline", "brief","url"
        )

        for t in tasks:
            # 转成 AI 模块所需的格式
            task_meta = {
                "id": f"{course_code}_{t['id']}",
                "task": f"{course_code} - {t['title']}",
                "dueDate": t["deadline"].isoformat() if t["deadline"] else None,
                "detailPdfPath":  t["url"], # 取出
                #"estimatedHours": 3     # 临时估计 3 小时，AI 模块会自动修正
            }
            tasks_meta.append(task_meta)

    #print("任务有:",tasks_meta)
    if not tasks_meta:
        return JsonResponse({"success": False, "message": "No tasks found"}, status=404)
    
    # 4️⃣ 调用 AI 模块生成学习计划
   

    try:
        print(tasks_meta)
        # 转换偏好数据格式以匹配AI模块期望的字段名
        ai_preferences = {
            "daily_hour_cap": int(preferences.get("dailyHours", 4)),
            "weekly_study_days": int(preferences.get("weeklyStudyDays", 5)),
            "avoid_days": preferences.get("avoidDays", [])
        }
        print(f"🤖 [GENERATE_AI_PLAN] AI模块偏好参数: {ai_preferences}")
        ai_result = generate_plan(ai_preferences, tasks_meta)
        print("🤖 AI generate!：")
        from pprint import pprint
        pprint(ai_result)
        # 直接返回结果
        return JsonResponse({"success": True, "message": "OK", "data": ai_result})

    except Exception as e:
        print("[AI_GENERATE_PLAN_ERROR]", str(e))
        return JsonResponse({
            "success": False,
            "message": f"AI Plan generation failed: {str(e)}"
        }, status=500)
@csrf_exempt
def save_weekly_plans(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    student_id = body.get("student_id")
    weekly_plans = body.get("weeklyPlans")
    tz = body.get("tz") or "Australia/Sydney"
    source = body.get("source") or "ai"

    if not student_id or not isinstance(weekly_plans, dict):
        return JsonResponse(
            {"ok": False, "error": "student_id and weeklyPlans are required"},
            status=400,
        )

    result = {"ok": True, "saved": [], "skipped": []}

    # 逐个 week_offset 处理
    for offset_key, items in weekly_plans.items():
        try:
            offset = int(offset_key)
        except Exception:
            result["skipped"].append({"offset_key": offset_key, "reason": "non-int key"})
            continue

        # 空周直接跳过（前端一般有 2、3 为空数组）
        if not items:
            result["skipped"].append({"offset": offset, "reason": "empty"})
            continue

        week_monday = _current_monday(offset).date()

        with transaction.atomic():
            # 1) upsert 头表
            plan, created = StudyPlan.objects.update_or_create(
                student_id=student_id,
                week_start_date=week_monday,
                defaults={
                    "week_offset": offset,
                    "tz": tz,
                    "source": source,
                },
            )

            # 2) 清空旧的明细（简单稳妥）
            StudyPlanItem.objects.filter(plan=plan).delete()

            # 3) 批量插入新的明细
            objs = []
            for it in items:
                # 字段映射：严格跟你前端一致
                external_item_id = str(it.get("id", "")).strip()
                course_code = str(it.get("courseId", "")).strip()
                course_title = (it.get("courseTitle") or "").strip()
                scheduled_date_str = it.get("date")  # "YYYY-MM-DD"
                try:
                    scheduled_date = date.fromisoformat(scheduled_date_str) if scheduled_date_str else week_monday
                except Exception:
                    scheduled_date = week_monday  # 兜底

                minutes = int(it.get("minutes") or 0)
                part_index = int(it.get("partIndex") or 0)
                parts_count = int(it.get("partsCount") or 0)
                part_title = (it.get("partTitle") or "").strip() or None
                color = (it.get("color") or "").strip() or None
                completed = bool(it.get("completed"))
                completed_at = timezone.now() if completed else None

                try:
                    parts = str(it.get("id", "")).split("-")
                    if len(parts) >= 2:
                        task_id = parts[1]  # 提取中间的编号
                except Exception:
                    task_id = None
                    
                objs.append(
                    StudyPlanItem(
                        plan=plan,
                        external_item_id=external_item_id,
                        course_code=course_code,
                        course_title=course_title or None,
                        scheduled_date=scheduled_date,
                        minutes=minutes,
                        part_index=part_index,
                        parts_count=parts_count,
                        part_title=part_title,
                        color=color,
                        completed=completed,
                        completed_at=completed_at,
                        task_id=task_id,
                    )
                )

            if objs:
                StudyPlanItem.objects.bulk_create(objs)

            result["saved"].append(
                {
                    "offset": offset,
                    "week_start_date": week_monday.isoformat(),
                    "plan_id": plan.id,
                    "created": created,
                    "items": len(objs),
                }
            )

    return JsonResponse(result, status=200)


@csrf_exempt
def get_all_weekly_plans(request):
    
    sid = _auth(request)
    if sid is None:
        return JsonResponse({"error": "Auth required"}, status=401)
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # 预取 items，并按日期 / part_index 排序，便于前端直接展示
    items_qs = StudyPlanItem.objects.order_by("scheduled_date", "part_index")
    plans = (
        StudyPlan.objects
        .filter(student_id=sid)
        .order_by("week_offset", "week_start_date")
        .prefetch_related(Prefetch("items", queryset=items_qs))
    )

    result = {}
    for plan in plans:
        wk = str(plan.week_offset)  # 与 localStorage 键保持一致：字符串键
        arr = result.setdefault(wk, [])
        for it in plan.items.all():
            arr.append({
                "id": it.external_item_id,          # PlanItem.id
                "courseId": it.course_code,
                "courseTitle": it.course_title or "",
                "date": it.scheduled_date.strftime("%Y-%m-%d"),
                "minutes": it.minutes,
                "partIndex": it.part_index,
                "partsCount": it.parts_count,
                "partTitle": it.part_title or "",
                "color": it.color or "",
                "completed": bool(it.completed),
            })
    print("现在从数据库读完了：",result)
    return JsonResponse({"success": True, "data": result})


