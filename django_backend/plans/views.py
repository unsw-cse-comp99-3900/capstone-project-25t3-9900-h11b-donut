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
        
        # 获取用户时区，默认使用Australia/Sydney
        tz = request.POST.get('timezone', request.GET.get('timezone', 'Australia/Sydney'))
        print(f"🌍 [GENERATE_AI_PLAN] 使用时区: {tz}")
        
        ai_result = generate_plan(ai_preferences, tasks_meta, user_timezone=tz)
        print("🤖 AI generate!：")
        from pprint import pprint
        pprint(ai_result)
        
        # 📥 构造AI详细内容用于数据库存储
        ai_details = {
            "aiSummary": ai_result.get("aiSummary", {}),
            "generationReason": f"AI-generated learning plan based on {len(tasks_meta)} course assignment PDFs and user preferences",
            "generationTime": timezone.now().isoformat(),
            "preferences": ai_preferences,
            "tasksAnalysis": tasks_meta
        }
        
        print("🤖 [GENERATE_AI_PLAN] 准备保存AI计划到数据库...")
        print("🔍 [GENERATE_AI_PLAN] AI结果结构:", list(ai_result.keys()) if isinstance(ai_result, dict) else type(ai_result))
        
        # 🔄 将AI结果映射为前端所需的格式并直接保存
        from .services import map_ai_result_to_weekly_format, _save_plan_to_database_directly
        try:
            print("🔄 [GENERATE_AI_PLAN] 开始映射AI结果...")
            weekly_plan = map_ai_result_to_weekly_format(ai_result, tz)
            print("✅ [GENERATE_AI_PLAN] AI结果映射完成")
            
            print("💾 [GENERATE_AI_PLAN] 开始保存到数据库...")
            # 保存到StudyPlan表（包含AI详细内容）
            save_result = _save_plan_to_database_directly(student, weekly_plan, ai_details)
            print("✅ [GENERATE_AI_PLAN] 保存操作完成:", save_result)
        except Exception as save_error:
            print(f"❌ [GENERATE_AI_PLAN] 保存过程出错: {save_error}")
            print(f"❌ [GENERATE_AI_PLAN] 错误类型: {type(save_error)}")
            import traceback
            traceback.print_exc()
            
            # 即使保存失败，也返回AI结果（不包含保存状态）
            return JsonResponse({
                "success": True, 
                "message": "AI计划生成成功，但保存失败", 
                "data": ai_result,
                "saved": False,
                "plan_id": None
            })
        
        if save_result["success"]:
            print("✅ [GENERATE_AI_PLAN] 计划已成功保存到数据库")
            
            # 同时保存到AI对话模块以供Explain功能使用
            try:
                from ai_chat.chat_service import AIChatService
                chat_service = AIChatService()
                chat_success = chat_service.save_study_plan(student, ai_result)
                if chat_success:
                    print("✅ [GENERATE_AI_PLAN] 计划已同步到AI对话模块")
                else:
                    print("⚠️ [GENERATE_AI_PLAN] 计划保存到AI对话模块失败")
            except Exception as chat_error:
                print(f"⚠️ [GENERATE_AI_PLAN] AI对话模块保存错误: {chat_error}")
            
            # 返回包含AI详细内容的完整数据给前端
            ai_result["aiDetails"] = ai_details
            return JsonResponse({
                "success": True, 
                "message": "OK", 
                "data": ai_result,
                "saved": True,
                "plan_id": save_result.get("plan_id")
            })
        else:
            print(f"❌ [GENERATE_AI_PLAN] 数据库保存失败: {save_result.get('error')}")
            return JsonResponse({
                "success": False,
                "message": f"Failed to save plan: {save_result.get('error')}"
            }, status=500)

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

    # 这三个字段是你前端想传的 AI 相关信息
    ai_details = body.get("aiDetails")
    generation_reason = body.get("generationReason", "")
    generation_time = body.get("generationTime")

    if not student_id or not isinstance(weekly_plans, dict):
        return JsonResponse(
            {"ok": False, "error": "student_id and weeklyPlans are required"},
            status=400,
        )

    result = {"ok": True, "saved": [], "skipped": []}

    # 🔴 关键修改：对当前学生，先把旧的 plan 和 plan_item 全部删掉，再重建
    with transaction.atomic():
        # 1) 找出该学生所有旧的 StudyPlan
        old_plans = StudyPlan.objects.filter(student_id=student_id)

        # 2) 删掉这些 plan 对应的所有 StudyPlanItem
        StudyPlanItem.objects.filter(plan__in=old_plans).delete()

        # 3) 再删掉所有旧的 StudyPlan
        old_plans.delete()

        # 4) 然后开始根据 weekly_plans 重新创建新的 plan + items
        for offset_key, items in weekly_plans.items():
            try:
                offset = int(offset_key)
            except Exception:
                result["skipped"].append(
                    {"offset_key": offset_key, "reason": "non-int key"}
                )
                continue

            # 空周直接跳过
            if not items:
                result["skipped"].append({"offset": offset, "reason": "empty"})
                continue

            # 这里仍然使用你原来的 _current_monday(offset) 逻辑
            week_monday = _current_monday(offset).date()

            # 准备 meta：把 AI 细节塞进去
            meta_data = None
            if ai_details and source == "ai":
                meta_data = {
                    "aiDetails": ai_details,
                    "generationReason": generation_reason,
                    "generationTime": generation_time,
                    "hasAIGeneration": True,
                }
                print("🤖 [SAVE_AI_DETAILS] 保存AI详细内容到meta字段")

            # 🔹 注意：这里用 create，而不是 update_or_create，
            # 因为我们已经把该学生的所有旧 plan 删干净了
            plan = StudyPlan.objects.create(
                student_id=student_id,
                week_start_date=week_monday,
                week_offset=offset,
                tz=tz,
                source=source,
                meta=meta_data,
            )

            objs = []
            for it in items:
                external_item_id = str(it.get("id", "")).strip()
                course_code = str(it.get("courseId", "")).strip()
                course_title = (it.get("courseTitle") or "").strip()
                scheduled_date_str = it.get("date")
                try:
                    scheduled_date = (
                        date.fromisoformat(scheduled_date_str)
                        if scheduled_date_str
                        else week_monday
                    )
                except Exception:
                    scheduled_date = week_monday

                minutes = int(it.get("minutes") or 0)
                part_index = int(it.get("partIndex") or 0)
                parts_count = int(it.get("partsCount") or 0)
                part_title = (it.get("partTitle") or "").strip() or None
                color = (it.get("color") or "").strip() or None
                completed = bool(it.get("completed"))
                completed_at = timezone.now() if completed else None

                # 从 id 中提 task_id（中间那段数字）
                task_id = None
                try:
                    parts = str(it.get("id", "")).split("-")
                    if len(parts) >= 2:
                        task_id = parts[1]
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
                    "created": True,  # 我们这里一定是新建
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

    return JsonResponse({"success": True, "data": result})


@csrf_exempt
def get_ai_plan_details(request: HttpRequest):
    """
    获取AI生成计划的详细内容，包括每个part的说明和生成原因
    前端用于显示给用户的详细解释
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    student_id = request.GET.get("student_id")
    week_offset = request.GET.get("week_offset")
    
    if not student_id:
        return JsonResponse({"error": "student_id is required"}, status=400)
    
    try:
        # 获取用户的计划
        query = StudyPlan.objects.filter(student_id=student_id)
        if week_offset:
            query = query.filter(week_offset=int(week_offset))
        
        plans = query.order_by("-created_at")
        
        result = []
        for plan in plans:
            plan_data = {
                "id": plan.id,
                "week_start_date": plan.week_start_date.isoformat(),
                "week_offset": plan.week_offset,
                "source": plan.source,
                "created_at": plan.created_at.isoformat(),
                "has_ai_details": False,
                "ai_details": None,
                "generation_reason": "",
                "items_with_details": []
            }
            
            # 检查是否有AI详细内容
            if plan.meta:
                try:
                    meta = plan.meta if isinstance(plan.meta, dict) else json.loads(plan.meta)
                    if meta.get("hasAIGeneration"):
                        plan_data["has_ai_details"] = True
                        plan_data["ai_details"] = meta.get("aiDetails", {})
                        plan_data["generation_reason"] = meta.get("generationReason", "")
                        plan_data["generation_time"] = meta.get("generationTime", "")
                        
                        # 为每个任务项添加AI详细说明
                        items = StudyPlanItem.objects.filter(plan=plan).order_by("scheduled_date", "part_index")
                        ai_summary = plan_data["ai_details"].get("aiSummary", {})
                        ai_tasks = ai_summary.get("tasks", [])
                        
                        # 建立任务ID到AI详细信息的映射
                        ai_task_map = {}
                        for ai_task in ai_tasks:
                            task_id_match = ai_task.get("taskId", "")
                            # 尝试匹配 external_item_id 的模式
                            for item in items:
                                if task_id_match in item.external_item_id:
                                    ai_task_map[item.external_item_id] = ai_task
                                    break
                        
                        for item in items:
                            item_data = {
                                "id": item.external_item_id,
                                "course_code": item.course_code,
                                "part_title": item.part_title,
                                "scheduled_date": item.scheduled_date.isoformat(),
                                "minutes": item.minutes,
                                "part_index": item.part_index,
                                "parts_count": item.parts_count,
                                "ai_notes": "",
                                "ai_explanation": ""
                            }
                            
                            # 添加AI详细说明
                            ai_task_info = ai_task_map.get(item.external_item_id)
                            if ai_task_info and "parts" in ai_task_info:
                                parts = ai_task_info["parts"]
                                for part in parts:
                                    if part.get("partId") == f"p{item.part_index + 1}" or \
                                       part.get("order") == item.part_index + 1:
                                        item_data["ai_notes"] = part.get("notes", "")
                                        break
                            
                            if ai_task_info:
                                item_data["ai_explanation"] = ai_task_info.get("explanation", "")
                            
                            plan_data["items_with_details"].append(item_data)
                
                except Exception as e:
                    print(f"[AI_DETAILS_ERROR] 解析AI详细内容失败: {e}")
            
            result.append(plan_data)
        
        return JsonResponse({"success": True, "data": result})
        
    except Exception as e:
        print("[GET_AI_PLAN_DETAILS_ERROR]", str(e))
        return JsonResponse({"error": f"Failed to get AI plan details: {str(e)}"}, status=500)


