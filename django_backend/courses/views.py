from django.shortcuts import render, redirect
from django.db import models, IntegrityError
from accounts.models import StudentAccount
from .models import Course, StudentCourse, Material


def choose_courses(request):
    # 登录保护
    if "student_id" not in request.session:
        return redirect("index")
    sid = request.session["student_id"]

    if request.method == "GET":
        return render(request, "choose_courses.html")

    # POST: 处理新增课程
    code = (request.POST.get("course_code") or "").strip().upper()
    if not code:
        return render(request, "choose_courses.html", {"message": "请输入课程代码。"})

    try:
        # 检查课程是否存在
        if not Course.objects.filter(course_code=code).exists():
            return render(request, "choose_courses.html", {"message": f"没有查询到该课程：{code}"})

        student = StudentAccount.objects.get(student_id=sid)
        course = Course.objects.get(course_code=code)

        # 检查是否已选
        if StudentCourse.objects.filter(student=student, course=course).exists():
            return redirect(f"/courses/materials/{code}?duplicated=1")

        StudentCourse.objects.create(student=student, course=course)
        ## 提示选课成功
        return redirect(f"/courses/materials/{code}?added=1")


    except IntegrityError:
        return render(request, "choose_courses.html", {"message": "选课失败，请稍后再试。"})


# def materials_of_course(request, course_code):
#     if "student_id" not in request.session:
#         return redirect("index")
#     code = (course_code or "").upper()
#     return render(request, "materials.html", {"code": code})

def materials_of_course(request, course_code):
    if "student_id" not in request.session:
        return redirect("index")

    code = (course_code or "").upper()

    # 查询资料表中该课程的所有资料（如果有）
    from .models import Material
    materials = Material.objects.filter(course__course_code=code).values("title", "url")

    # 读取 URL 参数 added / duplicated
    added = request.GET.get("added")
    duplicated = request.GET.get("duplicated")

    return render(request, "materials.html", {
        "code": code,
        "materials": materials,
        "added": added,
        "duplicated": duplicated
    })


def show_my_material(request, course_code):
    if "student_id" not in request.session:
        return redirect("index")
    code = (course_code or "").upper()
    return render(request, "show_my_material.html", {"code": code})
