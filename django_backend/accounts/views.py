from django.shortcuts import render, redirect
from django.db import IntegrityError
import bcrypt
from .models import StudentAccount
from django.db import models  
from django.conf import settings
from courses.models import StudentCourse, Course
from preferences.models import StudentWeeklyPreference


def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method != "POST":
        return redirect("index")

    student_id = (request.POST.get("student_id") or "").strip()
    email = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""

    if not student_id or not email or not password:
        return render(request, "index.html", {"message": "Please enter your zid, email and password"})

    try:
        # bcrypt 哈希加密
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # 写入数据库
        StudentAccount.objects.create(student_id=student_id, email=email, password_hash=hashed)

        return render(request, "index.html", {"message": "注册成功！"})

    except IntegrityError:
        return render(request, "index.html", {"message": "学号或邮箱已存在，请更换后再试。"})

    except Exception as e:
        print("[REGISTER ERROR]", repr(e))
        return render(request, "index.html", {"message": "注册失败：服务器内部错误，请检查后端日志。"})


def login_view(request):
    if request.method != "POST":
        return redirect("index")

    identifier = (request.POST.get("identifier") or "").strip()
    password = request.POST.get("password") or ""

    if not identifier or not password:
        return render(request, "index.html", {"message": "请填写账号和密码。"})

    try:
        # 用学号或邮箱查找
        row = StudentAccount.objects.filter(
            models.Q(student_id=identifier) | models.Q(email=identifier)
        ).values("student_id", "email", "password_hash").first()

        if not row:
            return render(request, "index.html", {"message": "账号不存在。"})

        # 检查 bcrypt 密码
        ok = bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
        if ok:
            # 登录成功，写入 session
            request.session["student_id"] = row["student_id"]
            return redirect("welcome")
        else:
            return render(request, "index.html", {"message": "密码错误，请重试。"})

    except Exception as e:
        print("[LOGIN ERROR]", repr(e))
        return render(request, "index.html", {"message": "登录失败，请检查后端日志。"})



## 验证用户的登录状态，并向已登录用户展示欢迎页面

# def welcome(request):
#     if "student_id" not in request.session:
#         return redirect("index")
#     sid = request.session["student_id"]
#     return render(request, "welcome.html", {"identifier": sid})

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


def logout_view(request):
    request.session.flush()
    return redirect("index")











