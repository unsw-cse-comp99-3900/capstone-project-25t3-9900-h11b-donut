from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Max
from .forms import PreferenceForm, days_to_bitmask
from .models import StudentWeeklyPreference
from accounts.models import StudentAccount

SEMESTER_CODE = "2025T1"

def save_prefs(request):
    if "student_id" not in request.session:
        return redirect("index")
    sid = request.session["student_id"]

    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid method"}, status=405)

    form = PreferenceForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "error": "Invalid form data"}, status=400)

    week_no = form.cleaned_data["week_no"]
    mode = form.cleaned_data["mode"]

    student = StudentAccount.objects.get(student_id=sid)

    if mode == "default":
        # 使用上一周的数据复制
        prev = StudentWeeklyPreference.objects.filter(
            student=student, semester_code=SEMESTER_CODE, week_no=week_no - 1
        ).first()
        if not prev:
            return JsonResponse({"ok": False, "error": "No previous week"}, status=400)

        StudentWeeklyPreference.objects.update_or_create(
            student=student,
            semester_code=SEMESTER_CODE,
            week_no=week_no,
            defaults={
                "daily_hours": prev.daily_hours,
                "weekly_study_days": prev.weekly_study_days,
                "avoid_days_bitmask": prev.avoid_days_bitmask,
                "mode": "default",
                "derived_from_week_no": week_no - 1
            }
        )
    else:
        # 手动模式：使用表单值
        daily_hours = form.cleaned_data.get("daily_hours") or 0.0
        weekly_study_days = form.cleaned_data.get("weekly_study_days") or 0
        avoid_days = form.cleaned_data.get("avoid_days") or []
        mask = days_to_bitmask(avoid_days)

        StudentWeeklyPreference.objects.update_or_create(
            student=student,
            semester_code=SEMESTER_CODE,
            week_no=week_no,
            defaults={
                "daily_hours": daily_hours,
                "weekly_study_days": weekly_study_days,
                "avoid_days_bitmask": mask,
                "mode": "manual",
                "derived_from_week_no": None
            }
        )

    return redirect("welcome")
