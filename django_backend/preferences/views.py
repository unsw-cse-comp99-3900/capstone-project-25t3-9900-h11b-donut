# preferences/views.py
import json
from decimal import Decimal
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from accounts.models import StudentAccount
from preferences.models import StudentPreference, StudentPreferenceDefault
from utils.auth import get_student_id_from_request

# 注意：模型注释写的是 0..6 表示 周日..周六
WEEK_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
LABEL_TO_INDEX = {name: i for i, name in enumerate(WEEK_LABELS)}

def labels_to_bitmask(days):
    """['Mon','Sun'] -> bitmask (Sun=0, Mon=1, ..., Sat=6)"""
    mask = 0
    for d in days or []:
        if isinstance(d, str):
            if d not in LABEL_TO_INDEX:
                raise ValueError(f"invalid day label: {d}")
            idx = LABEL_TO_INDEX[d]
        else:
            # 兼容数字 0..6
            idx = int(d)
            if idx < 0 or idx > 6:
                raise ValueError(f"invalid day index: {d}")
        mask |= (1 << idx)
    return mask

def bitmask_to_labels(mask: int):
    out = []
    for i, name in enumerate(WEEK_LABELS):
        if mask & (1 << i):
            out.append(name)
    return out

def _ok(data=None):
    return JsonResponse({"success": True, "data": data})

def _err(msg, status=400):
    return JsonResponse({"success": False, "message": msg}, status=status)

@csrf_exempt
def preferences_entry(request: HttpRequest):
    """
    - GET  /api/preferences      读取：优先 default，再用 current；无则返回 data=None
    - PUT  /api/preferences      保存：saveAsDefault 为真存入 Default 表，否则存入 Current 表
      
        dailyHours: number (0.25~24)
        weeklyStudyDays: number (1~7)
        avoidDays: string[] in ["Sun","Mon",...,"Sat"]  (也兼容数字 0..6)
        saveAsDefault: boolean
        description: string | null
    """
    # 1) 鉴权：从 Bearer Token 中解析 student_id
    student_id = get_student_id_from_request(request)
    if not student_id:
        return _err("Unauthorized", 401)

    # 2) 获取学生
    try:
        student = StudentAccount.objects.get(student_id=student_id)
    except StudentAccount.DoesNotExist:
        return _err("Student not found", 404)

    # ---------- GET ----------
    if request.method == "GET":
        # 优先默认
        pref = StudentPreferenceDefault.objects.filter(student=student).first()
        source = "default"
        if not pref:
            # 其次当前
            pref = StudentPreference.objects.filter(student=student).first()
            source = "current"

        if not pref:
            return _ok(None)

        data = {
            "source": source,
            "dailyHours": float(pref.daily_hours) if pref.daily_hours is not None else None,
            "weeklyStudyDays": int(pref.weekly_study_days) if pref.weekly_study_days is not None else None,
            "avoidDays": bitmask_to_labels(int(pref.avoid_days_bitmask or 0)),
            "saveAsDefault": (source == "default"),
            "description": pref.description or "",
        }
        return _ok(data)

    # ---------- PUT ----------
    if request.method != "PUT":
        return _err("Method Not Allowed", 405)

    # 3) 解析 JSON
    try:
        body = json.loads((request.body or b"").decode("utf-8") or "{}")
    except Exception:
        return _err("Invalid JSON", 400)

    daily_hours       = body.get("dailyHours")
    weekly_study_days = body.get("weeklyStudyDays")
    avoid_days_list   = body.get("avoidDays") or []
    save_as_default   = bool(body.get("saveAsDefault"))
    description       = (body.get("description") or "").strip()

    # 4) 校验（与模型约束一致）
    # daily_hours: Decimal(0.25~24)
    try:
        dh = Decimal(str(daily_hours))
        if dh < Decimal("0.25") or dh > Decimal("24"):
            raise ValueError
    except Exception:
        return _err("dailyHours must be between 0.25 and 24", 400)

    # weekly_study_days: int 1..7
    try:
        wsd = int(weekly_study_days)
        if wsd < 1 or wsd > 7:
            raise ValueError
    except Exception:
        return _err("weeklyStudyDays must be an integer between 1 and 7", 400)

    # avoidDays: labels subset / or 0..6
    try:
        mask = labels_to_bitmask(avoid_days_list)
    except ValueError as ve:
        return _err(str(ve), 400)

    # 5) 落库：根据 saveAsDefault 决定写哪张表（默认 or 当前）
    try:
        with transaction.atomic():
            if save_as_default:
                # 写默认表（OneToOne：每个学生最多一条）
                StudentPreferenceDefault.objects.update_or_create(
                    student=student,
                    defaults=dict(
                        daily_hours=dh,
                        weekly_study_days=wsd,
                        avoid_days_bitmask=mask,
                        description=description,
                    ),
                )
            else:
                # 写当前表
                StudentPreference.objects.update_or_create(
                    student=student,
                    defaults=dict(
                        daily_hours=dh,
                        weekly_study_days=wsd,
                        avoid_days_bitmask=mask,
                        description=description,
                    ),
                )
    except Exception as e:
        print("[PREFERENCES_SAVE_ERROR]", repr(e))
        return _err("Server Error", 500)

    return _ok()
