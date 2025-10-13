from django.shortcuts import render, redirect
from django.db import IntegrityError
import bcrypt
from .models import StudentAccount
from django.db import models  
from django.conf import settings
from courses.models import StudentCourse, Course
from preferences.models import StudentWeeklyPreference
from django.http import JsonResponse, HttpRequest
import json
from django.views.decorators.csrf import csrf_exempt

def api_ok(data=None, message="OK", status=200):
    return JsonResponse({"success": True, "message": message, "data": data}, status=status)

def api_err(message="Bad Request", status=400):
    return JsonResponse({"success": False, "message": message, "data": None}, status=status)

def _json_body(request: HttpRequest):
    """安全解析 JSON 请求体"""
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}

@csrf_exempt
def register_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        student_id = (data.get("student_id") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""

        if not student_id or not email or not password:
            return JsonResponse({"success": False, "message": "Please enter zid, email and password"}, status=400)

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        StudentAccount.objects.create(
            student_id=student_id,
            email=email,
            password_hash=hashed
        )

        return JsonResponse({"success": True, "message": "Registered successfully"}, status=201)

    except IntegrityError:
        return JsonResponse({"success": False, "message": "Student ID or email already exists"}, status=409)

    except Exception as e:
        print("[REGISTER ERROR]", repr(e))
        return JsonResponse({"success": False, "message": "Internal server error"}, status=500)
    
@csrf_exempt
def login_api(request: HttpRequest):
    if request.method != "POST":
        return api_err("Method Not Allowed", 405)

    body = _json_body(request)
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""

    if not email or not password:
        return api_err("email and password are required")

    try:
        row = StudentAccount.objects.filter(email=email).values(
            "student_id", "email", "password_hash"
        ).first()
        if not row:
            return api_err("Invalid email or password", 401)

        ok = bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
        if not ok:
            return api_err("Invalid email or password", 401)

        # 登录成功：先用一个固定 token（后续我们再改成数据库存的真 token）
        token = "dev-token"

        user_payload = {
            "studentId": row["student_id"],
            "email": row["email"],
        }

        return api_ok({"token": token, "user": user_payload})

    except Exception as e:
        print("[API LOGIN ERROR]", repr(e))
        return api_err("Server Error", 500)

@csrf_exempt
def logout_api(request: HttpRequest):
    
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed", "data": None}, status=405)
    
    # 清空 session
    request.session.flush()

    return JsonResponse({"success": True, "message": "Logged out successfully", "data": None})





def index(request):
    return render(request, 'index.html')






def welcome(request):
    if "student_id" not in request.session:
        return redirect("index")

    sid = request.session["student_id"]

    # 查询学生的所有课程
    courses = StudentCourse.objects.filter(student__student_id=sid).select_related('course')

    # 查询最近一周的学习偏好
    pref = StudentWeeklyPreference.objects.filter(
        student__student_id=sid, semester_code="2025T1"
    ).order_by("-week_no").first()

    # 计算当前周
    if pref:
        current_week = min(10, pref.week_no + 1)
    else:
        current_week = 1

    # ✅ 新增：如果有偏好记录，就把 bitmask 转成 ['Sat','Sun']
    WEEK_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if pref:
        pref.avoid_days_list = [
            day for i, day in enumerate(WEEK_LABELS)
            if pref.avoid_days_bitmask & (1 << i)
        ]

    return render(request, "welcome.html", {
        "identifier": sid,
        "courses": courses,
        "pref": pref,
        "semester": "2025T1",
        "current_week": current_week
    })













