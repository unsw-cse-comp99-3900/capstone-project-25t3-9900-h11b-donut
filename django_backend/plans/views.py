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
    Return the currently logged in student ID.
Prioritize using the session, and then try to check the database from Authorization: Bearer<token>
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


PLANS_BY_STUDENT: Dict[str, Dict[int, List[Dict]]] = {}

def _current_monday(offset: int) -> datetime:
    now = datetime.now()
    # Python weekday(): Monday=0 .. Sunday=6
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    monday = monday + timedelta(days=offset*7)
    return monday

def _gen_parts_for_task(course_id: str, task: Dict) -> List[Dict]:
    
    titles = ["Part 1 - Preparation", "Part 2 - Execution", "Part 3 - Review"]
    minutes = [30, 40, 20]
    parts = []
    for idx, (tt, mm) in enumerate(zip(titles, minutes), start=1):
        parts.append({
            "id": f"{course_id}-{task['id']}",  
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
        # already has plan.return
        existing = PLANS_BY_STUDENT.get(sid, {}).get(week_offset)
        if existing is not None:
            return _ok(existing)

        # Assuming the plan has been generated: generate parts for the current student's' My Course 'and distribute them to the current week
        my_course_ids = MY_COURSES_BY_STUDENT.get(sid, [])
        if not my_course_ids:
            return _ok([])

        monday = _current_monday(week_offset)

        day_ptr = 0
        items: List[Dict] = []
        for cid in my_course_ids:
            tasks = TASKS_BY_COURSE.get(cid, [])
            for t in tasks:
                for part in _gen_parts_for_task(cid, t):
                    date = monday + timedelta(days=day_ptr % 7)
                    items.append({**part, "date": date.strftime("%Y-%m-%d")})
                    day_ptr += 1

        PLANS_BY_STUDENT.setdefault(sid, {})[week_offset] = items
        return _ok(items)

    if request.method == "PUT":
        # save(overwrite)plan
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
    """courses + preferences + AI"""
    print(f"🚀 [GENERATE_AI_PLAN] get request: {request.method}")
    print(f"🚀 [GENERATE_AI_PLAN] Headers: {dict(request.headers)}")
    
    sid = get_student_id_from_request(request)
    print(f"🚀 [GENERATE_AI_PLAN] student ID: {sid}")
    
    if not sid:
        print("❌ [GENERATE_AI_PLAN] unauthorize")
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=401)
    try:
        student = StudentAccount.objects.get(student_id=sid)
    except StudentAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Student not found"}, status=404)
    
    pref = StudentPreference.objects.filter(student=student).first()
    pref_source = "current"
    if not pref:
        pref = StudentPreferenceDefault.objects.filter(student=student).first()
        pref_source = "default"
    
    print(f"📋 [GENERATE_AI_PLAN] preference from: {pref_source}")
    if pref:
        print(f"📋 [GENERATE_AI_PLAN] original preference: daily_hours={pref.daily_hours}, weekly_study_days={pref.weekly_study_days}, avoid_days_bitmask={pref.avoid_days_bitmask}")
    else:
        print(f"📋 [GENERATE_AI_PLAN] no preference, use default preference")
    

    if pref:
        WEEK_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        preferences = {
            "dailyHours": float(pref.daily_hours or 4),  
            "weeklyStudyDays": int(pref.weekly_study_days or 5),
            "avoidDays": [],
        }

        mask = int(pref.avoid_days_bitmask or 0)
        for i in range(7):  # 0=Sun, 6=Sat
            if mask & (1 << i):
                preferences["avoidDays"].append(WEEK_LABELS[i])
    else:
        preferences = {
        "dailyHours": 4,  
        "weeklyStudyDays": 5,  
        "avoidDays": ["Sun", "Sat"], 
    }
    print(f"📋 [GENERATE_AI_PLAN] final preference: {preferences}")
    print(f"📋 [GENERATE_AI_PLAN] preference from: {pref_source if 'pref_source' in locals() else 'unknown'}")


    from courses.models import StudentEnrollment, CourseTask

    enrolled_courses = StudentEnrollment.objects.filter(student_id=sid).values_list("course_code", flat=True)
    
    tasks_meta = []
    for course_code in enrolled_courses:

        tasks = CourseTask.objects.filter(course_code=course_code).values(
            "id", "title", "deadline", "brief","url"
        )

        for t in tasks:
            # format transform(AI need)
            task_meta = {
                "id": f"{course_code}_{t['id']}",
                "task": f"{course_code} - {t['title']}",
                "dueDate": t["deadline"].isoformat() if t["deadline"] else None,
                "detailPdfPath":  t["url"], 
            }
            tasks_meta.append(task_meta)

    if not tasks_meta:
        return JsonResponse({"success": False, "message": "No tasks found"}, status=404)
    
    try:
        print(tasks_meta)
        # Convert preference data format to match the expected field names of the AI module
        ai_preferences = {
            "daily_hour_cap": int(preferences.get("dailyHours", 4)),
            "weekly_study_days": int(preferences.get("weeklyStudyDays", 5)),
            "avoid_days": preferences.get("avoidDays", [])
        }
        print(f"🤖 [GENERATE_AI_PLAN] AI pref: {ai_preferences}")
        
        # Get user time zone, default to Australia/Sydney
        tz = request.POST.get('timezone', request.GET.get('timezone', 'Australia/Sydney'))
        print(f"🌍 [GENERATE_AI_PLAN] timezone:: {tz}")
        
        ai_result = generate_plan(ai_preferences, tasks_meta, user_timezone=tz)
        print("🤖 AI generate!：")
        from pprint import pprint
        pprint(ai_result)
        
        ai_details = {
            "aiSummary": ai_result.get("aiSummary", {}),
            "generationReason": f"AI-generated learning plan based on {len(tasks_meta)} course assignment PDFs and user preferences",
            "generationTime": timezone.now().isoformat(),
            "preferences": ai_preferences,
            "tasksAnalysis": tasks_meta
        }
        
        print("🤖 [GENERATE_AI_PLAN] prepare to write into db...")
        print("🔍 [GENERATE_AI_PLAN] AI result:", list(ai_result.keys()) if isinstance(ai_result, dict) else type(ai_result))
        
        #  Map AI results to the format required by the frontend and save them directly
        from .services import map_ai_result_to_weekly_format, _save_plan_to_database_directly
        try:
            print("🔄 [GENERATE_AI_PLAN] starting Mapping")
            weekly_plan = map_ai_result_to_weekly_format(ai_result, tz)
            print("✅ [GENERATE_AI_PLAN] Mapping done")
            
            print("💾 [GENERATE_AI_PLAN] prepare to write into db...")
            save_result = _save_plan_to_database_directly(student, weekly_plan, ai_details)
            print("✅ [GENERATE_AI_PLAN] save done:", save_result)
        except Exception as save_error:
            print(f"❌ [GENERATE_AI_PLAN] error during saving: {save_error}")
            print(f"❌ [GENERATE_AI_PLAN] error type: {type(save_error)}")
            import traceback
            traceback.print_exc()
            

            return JsonResponse({
                "success": True, 
                "message": "AI plan generate! but fail to save", 
                "data": ai_result,
                "saved": False,
                "plan_id": None
            })
        
        if save_result["success"]:
            print("✅ [GENERATE_AI_PLAN] save to db!")
            
            # Simultaneously save to AI dialogue module for use in Explain function
            try:
                from ai_chat.chat_service import AIChatService
                chat_service = AIChatService()
                chat_success = chat_service.save_study_plan(student, ai_result)
                if chat_success:
                    print("✅ [GENERATE_AI_PLAN] The plan has been synchronized to the AI dialogue module")
                else:
                    print("⚠️ [GENERATE_AI_PLAN] Failed to save plan to AI dialogue module")
            except Exception as chat_error:
                print(f"⚠️ [GENERATE_AI_PLAN] AI dialogue module saving error: {chat_error}")
            
            # Return complete data containing detailed AI content to the frontend
            ai_result["aiDetails"] = ai_details
            return JsonResponse({
                "success": True, 
                "message": "OK", 
                "data": ai_result,
                "saved": True,
                "plan_id": save_result.get("plan_id")
            })
        else:
            print(f"❌ [GENERATE_AI_PLAN] Database save failed: {save_result.get('error')}")
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

    ai_details = body.get("aiDetails")
    generation_reason = body.get("generationReason", "")
    generation_time = body.get("generationTime")

    if not student_id or not isinstance(weekly_plans, dict):
        return JsonResponse(
            {"ok": False, "error": "student_id and weeklyPlans are required"},
            status=400,
        )

    result = {"ok": True, "saved": [], "skipped": []}

 
    with transaction.atomic():
        # 1) find old StudyPlan
        old_plans = StudyPlan.objects.filter(student_id=student_id)

        # 2) delete StudyPlanItem
        StudyPlanItem.objects.filter(plan__in=old_plans).delete()

        # 3) then deleteStudyPlan
        old_plans.delete()

        # 4)create new plan + items
        for offset_key, items in weekly_plans.items():
            try:
                offset = int(offset_key)
            except Exception:
                result["skipped"].append(
                    {"offset_key": offset_key, "reason": "non-int key"}
                )
                continue

            # skip empty week
            if not items:
                result["skipped"].append({"offset": offset, "reason": "empty"})
                continue

        
            week_monday = _current_monday(offset).date()

         
            meta_data = None
            if ai_details and source == "ai":
                meta_data = {
                    "aiDetails": ai_details,
                    "generationReason": generation_reason,
                    "generationTime": generation_time,
                    "hasAIGeneration": True,
                }
                print("🤖 [SAVE_AI_DETAILS] save details!")


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

                # get taskid
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
                    "created": True,  
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

    # Pre fetch items and sort them by date/part_index for easy front-end display
    items_qs = StudyPlanItem.objects.order_by("scheduled_date", "part_index")
    plans = (
        StudyPlan.objects
        .filter(student_id=sid)
        .order_by("week_offset", "week_start_date")
        .prefetch_related(Prefetch("items", queryset=items_qs))
    )

    result = {}
    for plan in plans:
        wk = str(plan.week_offset)  
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
    Obtain detailed information on the AI generation plan, including explanations for each part and the reasons for its generation
Front end is used to display detailed explanations to users
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    student_id = request.GET.get("student_id")
    week_offset = request.GET.get("week_offset")
    
    if not student_id:
        return JsonResponse({"error": "student_id is required"}, status=400)
    
    try:
        # get user's plan
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
            
            # Check for detailed AI content
            if plan.meta:
                try:
                    meta = plan.meta if isinstance(plan.meta, dict) else json.loads(plan.meta)
                    if meta.get("hasAIGeneration"):
                        plan_data["has_ai_details"] = True
                        plan_data["ai_details"] = meta.get("aiDetails", {})
                        plan_data["generation_reason"] = meta.get("generationReason", "")
                        plan_data["generation_time"] = meta.get("generationTime", "")
                        
                        # Add detailed AI instructions for each task item
                        items = StudyPlanItem.objects.filter(plan=plan).order_by("scheduled_date", "part_index")
                        ai_summary = plan_data["ai_details"].get("aiSummary", {})
                        ai_tasks = ai_summary.get("tasks", [])
                        
                        # Establish a mapping from task ID to AI detailed information
                        ai_task_map = {}
                        for ai_task in ai_tasks:
                            task_id_match = ai_task.get("taskId", "")
                            # Attempt to match the pattern of external_item_id
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
                            
                            # clarification
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
                    print(f"[AI_DETAILS_ERROR] Failed to parse the detailed content of AI: {e}")
            
            result.append(plan_data)
        
        return JsonResponse({"success": True, "data": result})
        
    except Exception as e:
        print("[GET_AI_PLAN_DETAILS_ERROR]", str(e))
        return JsonResponse({"error": f"Failed to get AI plan details: {str(e)}"}, status=500)


