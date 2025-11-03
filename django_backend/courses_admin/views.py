import logging
import json
import os
from urllib.parse import unquote
from datetime import date
from django.conf import settings
from django.http import JsonResponse
from .models import CourseAdmin  # 假设你的表名是 courses_admin
from django.views.decorators.csrf import csrf_exempt
from django.db.models import OuterRef, Exists,Count
from courses.models import CourseCatalog,StudentEnrollment,CourseTask,Material,Question,QuestionChoice,QuestionKeyword,QuestionKeywordMap
from django.db import transaction,IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.http import FileResponse, Http404
import urllib.parse
import os

logger = logging.getLogger(__name__)
def ok(data): 
    return JsonResponse({"success": True, "data": data, "message": ""})
def err(message, status=400):
    return JsonResponse({"success": False, "data": None, "message": message}, status=status)
def courses_admin(request):
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)


    admin_id = request.GET.get('admin_id')
    if not admin_id:
        return JsonResponse({"success": True, "data": []})

    rows = CourseAdmin.objects.filter(admin_id=admin_id).values('admin_id', 'code')
    data = list(rows)
    codes = [row['code'] for row in data]
    if not codes:
        return JsonResponse({"success": True, "data": []})
    
    course_map = {
        c['code']: c
        for c in CourseCatalog.objects.filter(code__in=codes).values('code', 'title', 'description','illustration')
    }
    enroll_counts_qs = (
        StudentEnrollment.objects
        .filter(course_code__in=codes)
        .values('course_code')
        .annotate(n=Count('student_id', distinct=True))
    )
    enroll_count_map = {row['course_code']: row['n'] for row in enroll_counts_qs}
    enriched = []
    enriched = []
    for row in data:
        code = row['code']
        c = course_map.get(code, {})
        enriched.append({
            "code": code,
            "title": c.get("title", ""),
            "description": c.get("description", ""),
            "illustration": c.get("illustration", ""),
            "student_count": enroll_count_map.get(code, 0),  # 新增：该课程的学生人数
        })
    
    return JsonResponse({"success": True, "data": enriched})
@csrf_exempt
def course_exists(request):
    code = (request.GET.get("code") or "").strip().upper()
    if not code:
        return JsonResponse({"success": False, "message": "missing code"}, status=400)
    exists = CourseCatalog.objects.filter(code=code).exists()
    return JsonResponse({
    "success": True,
    "data": { "exists": exists }
})
@csrf_exempt
def create_course(request):
    # 1) 取参（form > json > query）
    admin_id = request.POST.get("admin_id") or request.GET.get("admin_id")
    code = request.POST.get("code") or request.GET.get("code")
    title = request.POST.get("title") or request.GET.get("title")
    description = request.POST.get("description") or request.GET.get("description") or ""
    # illustration 可选：如果你的 CourseCatalog 有这个字段就用；没有就忽略
    illustration = request.POST.get("illustration") or request.GET.get("illustration")

    if (not admin_id or not code or not title) and request.body:
        try:
            data = json.loads(request.body.decode("utf-8"))
            admin_id = admin_id or data.get("admin_id")
            code = code or data.get("code")
            title = title or data.get("title")
            description = description or data.get("description") or ""
            illustration = illustration or data.get("illustration")
        except Exception:
            pass

    code = (code or "").strip().upper()
    title = (title or "").strip()
    description = (description or "").strip()

    if not admin_id or not code or not title:
        return JsonResponse({"success": False, "message": "缺少参数：admin_id / code / title"}, status=400)

    # 2) 事务内创建或更新课程 + 关联管理员
    try:
        with transaction.atomic():
            # 2.1 创建或更新课程（幂等）
            defaults = {"title": title, "description": description}
            # 仅当模型真的有 illustration 字段时才写入，避免 AttributeError
            if illustration is not None and hasattr(CourseCatalog, "_meta") and any(
                f.name == "illustration" for f in CourseCatalog._meta.fields
            ):
                defaults["illustration"] = illustration

            course, created = CourseCatalog.objects.get_or_create(code=code, defaults=defaults)
            if not created:
                # 更新基础信息（只更新传入的字段）
                course.title = title
                course.description = description
                if illustration is not None and hasattr(CourseCatalog, "_meta") and any(
                    f.name == "illustration" for f in CourseCatalog._meta.fields
                ):
                    setattr(course, "illustration", illustration)
                course.save()

            # 2.2 建立管理员与课程的关联（外键字段名是 code）
            CourseAdmin.objects.get_or_create(admin_id=admin_id, code=course)

        return JsonResponse({
            "success": True,
            "message": f"课程 {code} 已{'创建' if created else '更新'}",
            "created": created
        })

    except IntegrityError as e:
        return JsonResponse({"success": False, "message": f"创建失败：{e}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"系统错误：{e}"}, status=500)
@csrf_exempt
def delete_course(request):
    # ---- Step 0. Method check ----
    if request.method not in ("DELETE", "POST"):
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    # ---- Step 1. 获取参数 ----
    admin_id = request.POST.get("admin_id") or request.GET.get("admin_id")
    course_code = request.POST.get("code") or request.GET.get("code")

    if (not admin_id or not course_code) and request.body:
        try:
            data = json.loads(request.body.decode("utf-8"))
            admin_id = admin_id or data.get("admin_id")
            course_code = course_code or data.get("code")
        except Exception:
            pass

    if not admin_id or not course_code:
        return JsonResponse({"success": False, "message": "wrong!"}, status=400)

    course = get_object_or_404(CourseCatalog, code=course_code)

    # 必须是这个课程的管理员
    if not CourseAdmin.objects.filter(admin_id=admin_id, code__code=course_code).exists():
        return JsonResponse({"success": False, "message": "wrong!"}, status=403)

    try:
        task_file_paths = []      # 任务附件 (TASK_ROOT/...)
        material_file_paths = []  # 课程资料 (MAT_ROOT/<course_code>/filename)

        with transaction.atomic():
            tasks = list(CourseTask.objects.filter(course_code=course_code))

            for t in tasks:
                task_id = t.id

                try:
                    from task_progress.models import TaskProgress as TPModel
                    TPModel.objects.filter(task_id=task_id).delete()
                except Exception:

                    pass

                task_url = getattr(t, "url", "") or ""
                if (
                    task_url
                    and hasattr(settings, "TASK_URL")
                    and hasattr(settings, "TASK_ROOT")
                    and task_url.startswith(settings.TASK_URL)
                ):
                    rel_path = task_url[len(settings.TASK_URL):].lstrip("/")
                    file_path = os.path.join(settings.TASK_ROOT, rel_path)
                    task_file_paths.append(file_path)

                t.delete()

            materials = list(Material.objects.filter(course_code=course_code))

            for m in materials:

                mat_url = (getattr(m, "url", "") or "").strip()
                mat_url = unquote(mat_url)

                filename = os.path.basename(mat_url)
                if filename and hasattr(settings, "MAT_ROOT"):
                    course_dir = os.path.join(settings.MAT_ROOT, course_code)
                    mat_file_path = os.path.join(course_dir, filename)
                    material_file_paths.append(mat_file_path)

                m.delete()

            questions = list(Question.objects.filter(course_code=course_code))
            for q in questions:
                q.delete()


            QuestionKeyword.objects.filter(
                ~Exists(
                    QuestionKeywordMap.objects.filter(keyword_id=OuterRef('pk'))
                )
            ).delete()
            StudentEnrollment.objects.filter(course_code=course_code).delete()
            CourseAdmin.objects.filter(code__code=course_code).delete()

            course.delete()

        for fpath in task_file_paths:
            try:
                if fpath and os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception as fe:
                print(f"[delete_course] task file delete failed: {fpath} err={fe}")

        for fpath in material_file_paths:
            try:
                if fpath and os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception as fe:
                print(f"[delete_course] material file delete failed: {fpath} err={fe}")

        return JsonResponse({"success": True, "message": f"课程 {course_code} 已成功删除"})

    except Exception as e:
        print("[delete_course] error:", e)
        return JsonResponse({"success": False, "message": f"删除失败：{e}"}, status=500)
@csrf_exempt
def course_tasks(request, course_id):
    
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        # 过滤出该课程下的任务
        tasks = CourseTask.objects.filter(course_code=course_id).values(
            "id",
            "title",
            "deadline",
            "brief",
            "percent_contribution",
            "url"
        )

        # 转成 list 并返回
        data = list(tasks)
        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        print("[course_tasks] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def course_students_progress(request, course_id: str):
    """管理员视角：获取课程下所有学生的加权进度与逾期数量。
    支持 query 参数 task_id：当提供时，返回该任务维度的进度与逾期；否则返回课程加权汇总。
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "GET method required"}, status=405)
    try:
        # 可选单任务视角
        task_id_qs = request.GET.get("task_id")
        task_filter = {"course_code": course_id}
        if task_id_qs:
            try:
                task_filter["id"] = int(task_id_qs)
            except Exception:
                pass
        # 课程任务列表（id, deadline, percent_contribution）
        tasks = list(CourseTask.objects.filter(**task_filter).values("id", "deadline", "percent_contribution"))
        task_ids = [t["id"] for t in tasks]

        # 选课学生列表（即使没有任务也返回学生占位数据）
        enrolls = list(StudentEnrollment.objects.filter(course_code=course_id).values("student_id"))
        student_ids = [e["student_id"] for e in enrolls]
        if not student_ids:
            return JsonResponse({"success": True, "data": []})

        # 学生姓名映射（可选）
        try:
            from stu_accounts.models import StudentAccount
            name_map = {
                s["student_id"]: s.get("name") or ""
                for s in StudentAccount.objects.filter(student_id__in=student_ids).values("student_id", "name")
            }
        except Exception:
            name_map = {}

        # 进度映射：student_id -> {task_id -> progress}
        try:
            from task_progress.models import TaskProgress as TP
        except Exception:
            TP = None
        rows = []
        if TP:
            rows = TP.objects.filter(task_id__in=task_ids, student_id__in=student_ids).values("student_id", "task_id", "progress")
        prog_map: dict[str, dict[int, int]] = {}
        for r in rows:
            sid = r["student_id"]
            tid = int(r["task_id"])  # 保证是 int
            prog_map.setdefault(sid, {})[tid] = int(r["progress"]) or 0

        today = date.today()
        result = []
        for sid in student_ids:
            task_prog = prog_map.get(sid, {})
            weight_sum = 0
            completed_weight = 0
            overdue_cnt = 0
            for t in tasks:
                w = int(t.get("percent_contribution") or 0)
                if w < 0:
                    w = 0
                weight_sum += w
                p = int(task_prog.get(int(t["id"]), 0))
                if p > 0:
                    completed_weight += w * min(p, 100) / 100.0
                # 逾期：截至今天过去的任务未满 100
                dl = t.get("deadline")
                if dl and dl < today:
                    if p < 100:
                        overdue_cnt += 1
            progress_pct = 0
            if weight_sum > 0:
                progress_pct = int(round(100.0 * completed_weight / weight_sum))
                progress_pct = max(0, min(100, progress_pct))
            result.append({
                "student_id": sid,
                "name": name_map.get(sid, ""),
                "progress": progress_pct,
                "overdue_count": overdue_cnt,
            })
        # 按姓名排序，空名用学号
        result.sort(key=lambda x: (x["name"] or x["student_id"]))
        return JsonResponse({"success": True, "data": result})
    except Exception as e:
        print("[course_students_progress] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def course_materials(request, course_id):
    
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        qs = (Material.objects
              .filter(course_code=course_id)
              .values("id", "course_code", "title", "url", "description")
              .order_by("id"))
        data = list(qs)
        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        print("[course_materials] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
@csrf_exempt
def course_questions(request, course_id):
    """
    GET /api/courses_admin/<course_id>/questions
    返回该课程的所有题目（含 choices、keywords）
    """
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        qs = (Question.objects
              .filter(course_code=course_id)
              .prefetch_related('choices')  
              .order_by('id'))

        data = []
        for q in qs:
            item = {
                "id": q.id,
                "qtype": q.qtype,                      # 'mcq' | 'short'
                "title": q.title,
                "description": q.description or "",
                "text": q.text,
                "keywords": (q.keywords_json or []),
            }
            if q.qtype == "mcq":
                item["choices"] = sorted([
                    {
                        "label": c.label or None,
                        "order": c.order,
                        "content": c.content,
                        "isCorrect": c.is_correct,
                    }
                    for c in q.choices.all()
                ], key=lambda x: x["order"])
            else:  # short answer
                item["answer"] = q.short_answer or ""

            data.append(item)

        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        print("[course_questions] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
@csrf_exempt
def create_course_question(request, course_code):
    """
    POST /api/courses_admin/<course_code>/questions/create
    创建题目及其选项、关键词映射。
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    qtype = body.get("qtype")
    if qtype not in ("mcq", "short"):
        return JsonResponse({"error": "qtype must be 'mcq' or 'short'"}, status=400)

    title = body.get("title") or ""
    description = body.get("description") or ""
    text = body.get("text") or ""
    short_answer = body.get("short_answer") or ""
    keywords = body.get("keywords") or []

    # 清洗关键词
    norm_keywords = []
    seen = set()
    for kw in keywords:
        if kw and isinstance(kw, str):
            clean = kw.strip()
            if clean and clean not in seen:
                seen.add(clean)
                norm_keywords.append(clean)

    try:
        with transaction.atomic():
            # 1️⃣ 创建 Question
            q = Question.objects.create(
                course_code=course_code,
                qtype=qtype,
                title=title,
                description=description,
                text=text,
                short_answer=short_answer if qtype == "short" else "",
                keywords_json=norm_keywords,
            )

            # 2️⃣ 若是选择题，写入 QuestionChoice
            if qtype == "mcq":
                choices = body.get("choices") or []
                if not choices:
                    return JsonResponse({"error": "mcq requires non-empty 'choices'"}, status=400)

                QuestionChoice.objects.bulk_create([
                    QuestionChoice(
                        question=q,
                        label=c.get("label"),
                        order=int(c.get("order", 0)),
                        content=c.get("content", ""),
                        is_correct=bool(c.get("is_correct")),
                    )
                    for c in choices
                ])

            # 3️⃣ 写入关键词表与映射表
            if norm_keywords:
                keyword_objs = []
                for name in norm_keywords:
                    kw, _ = QuestionKeyword.objects.get_or_create(name=name)
                    keyword_objs.append(kw)

                QuestionKeywordMap.objects.bulk_create([
                    QuestionKeywordMap(question=q, keyword=kw)
                    for kw in keyword_objs
                ])

        return JsonResponse({"success": True, "data": {"id": q.id}}, status=201)

    except Exception as e:
        print("[create_course_question] error:", e)
        return JsonResponse({"success": False, "message": "mcq requires non-empty 'choices'"}, status=400)

@csrf_exempt
@transaction.atomic
def update_course_question(request, course_id, question_id):
    
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "PUT method required", "data": None}, status=405)

    # 解析 JSON
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON", "data": None}, status=400)

    # 取题目
    q = get_object_or_404(Question, id=question_id, course_code=course_id)

    
    qtype = data.get("qtype")
    if qtype not in ("mcq", "short"):
        return JsonResponse({"success": False, "message": "Invalid qtype", "data": None}, status=400)

    title = (data.get("title") or "").strip()
    text  = (data.get("text")  or "").strip()
    if not title or not text:
        return JsonResponse({"success": False, "message": "title and text are required", "data": None}, status=400)

    #先更新 Question 主表 
    q.qtype       = qtype
    q.title       = title
    q.description = data.get("description") or ""
    q.text        = text

    # keywords：不单独封装函数，直接在此就地处理
    # 接受 list[str] 或 逗号字符串；做简单清洗：strip、lower、去空、去重（保持顺序）
    raw_kw = data.get("keywords")
    if isinstance(raw_kw, str):
        kw_list = [s.strip().lower() for s in raw_kw.split(",")]
    elif isinstance(raw_kw, list):
        kw_list = [str(s).strip().lower() for s in raw_kw]
    else:
        kw_list = []
    seen = set()
    keywords_list = []
    for k in kw_list:
        if k and k not in seen:
            seen.add(k)
            keywords_list.append(k)

    q.keywords_json = keywords_list

    if qtype == "short":
        q.short_answer = (data.get("answer") or "").strip()
        if not q.short_answer:
            return JsonResponse({"success": False, "message": "answer required for short question", "data": None}, status=400)
    else:
        q.short_answer = ""

    q.save()

    # 重建关键词映射 #
    QuestionKeywordMap.objects.filter(question=q).delete()
    if keywords_list:
        kw_objs = []
        for name in keywords_list:
            kw, _ = QuestionKeyword.objects.get_or_create(name=name)
            kw_objs.append(kw)
        QuestionKeywordMap.objects.bulk_create(
            [QuestionKeywordMap(question=q, keyword=kw) for kw in kw_objs],
            ignore_conflicts=True
        )
    QuestionKeyword.objects.filter(
        ~Exists(QuestionKeywordMap.objects.filter(keyword_id=OuterRef('pk')))
    ).delete()#清除无映射的keyword
    #处理选项 #
    if qtype == "mcq":
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            return JsonResponse({"success": False, "message": "choices required for mcq", "data": None}, status=400)

        # 至少两个非空 content
        filled_cnt = sum(1 for c in choices if str(c.get("content", "")).strip())
        if filled_cnt < 2:
            return JsonResponse({"success": False, "message": "at least two non-empty choices are required", "data": None}, status=400)

        if not any(bool(c.get("isCorrect")) for c in choices):
            return JsonResponse({"success": False, "message": "one correct choice required", "data": None}, status=400)

        # 清空旧选项并重建
        q.choices.all().delete()

        to_create = []
        for c in choices:
            content = str(c.get("content", "")).strip()
            if not content:
                continue
            to_create.append(QuestionChoice(
                question=q,
                label=(c.get("label") or None),
                order=int(c.get("order", 0) or 0),
                content=content,
                is_correct=bool(c.get("isCorrect", False))
            ))
        # 保证 order 递增，避免 unique_together 冲突
        to_create.sort(key=lambda x: x.order)
        QuestionChoice.objects.bulk_create(to_create)
    else:
        # 简答题：删除所有旧选项
        q.choices.all().delete()

    return JsonResponse({
        "success": True,
        "message": "Updated successfully",
        "data": {
            "id": q.id,
            "course_code": q.course_code,
            "qtype": q.qtype,
            "title": q.title,
            "description": q.description,
            "text": q.text,
            "keywords": q.keywords_json,
            "short_answer": q.short_answer if q.qtype == "short" else "",
        }
    })
@csrf_exempt
def delete_course_question(request, course_id, question_id):
    """
    DELETE /api/courses_admin/<course_id>/questions/<question_id>
    删除题目及关联项（choices、keywords）
    """
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE method required"}, status=405)

    try:
        q = Question.objects.get(id=question_id, course_code=course_id)
        q.delete()  # 自动级联删除 choices 和 keyword_map
        QuestionKeyword.objects.filter(
            ~Exists(
                QuestionKeywordMap.objects.filter(keyword_id=OuterRef('pk'))
            )
        ).delete()#删除keyword
        return JsonResponse({"success": True})
    except Question.DoesNotExist:
        return JsonResponse({"success": False, "message": "Question not found"}, status=404)
    except Exception as e:
        print("[delete_course_question] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
@csrf_exempt
def upload_task_file(request):
    if request.method != "POST":
        return err("Method not allowed", 405)

    f = request.FILES.get("file")
    if not f:
        return err("file is required")

    course = (request.POST.get("course") or "common").strip().lower()

   
    subdir = os.path.join(course)
    save_dir = os.path.join(settings.TASK_ROOT, subdir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f.name
    save_path = os.path.join(save_dir, filename)

    with open(save_path, "wb+") as dst:
        for chunk in f.chunks():
            dst.write(chunk)

    #  返回 task URL
    url_path = f"{settings.TASK_URL}{course}/{filename}".replace("\\", "/")

    return ok({
        "url": url_path,
        "filename": filename,
        "size": f.size,
    })
@csrf_exempt
def create_course_tasks(request, course_id: str):
    if request.method != "POST":
        return err("Method not allowed", 405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err("invalid json body")

    title = (body.get("title") or "").strip()
    if not title:
        return err("title is required")

    deadline_raw = body.get("deadline")
    if not deadline_raw:
        return err("deadline is required (YYYY-MM-DD)")
    deadline = parse_date(str(deadline_raw))
    if deadline < date.today():
        return err("deadline cannot be in the past")
    if not deadline:
        return err("deadline must be YYYY-MM-DD")

    brief = (body.get("brief") or "").strip()
    url = body.get("url") or None

    try:
        pc = int(body.get("percent_contribution", 100))
    except Exception:
        return err("percent_contribution must be an integer")
    if pc < 0 or pc > 100:
        return err("percent_contribution must be in [0,100]")

    t = CourseTask.objects.create(
        course_code=course_id,
        title=title,
        deadline=deadline,
        brief=brief,
        percent_contribution=pc,
        url=url,
    )
    return ok({"id": t.id})
@csrf_exempt
def delete_course_task(request, course_id, task_id):
    try:
        if request.method not in ("DELETE", "POST"):
            return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

        from django.db import transaction
        import os
        from django.conf import settings

        delete_file = request.GET.get("delete_file") in ("1", "true", "True")

        with transaction.atomic():
            task = CourseTask.objects.filter(id=task_id, course_code=course_id).first()
            if not task:
                return JsonResponse({"success": False, "message": "Task not found"}, status=404)

            # 删除进度（如果 task_progress 应用存在）
            try:
                from task_progress.models import TaskProgress as TP3
                TP3.objects.filter(task_id=task_id).delete()
            except Exception:
                pass

            # 附件路径
            file_path = None
            if delete_file and task.url:
                if task.url.startswith(settings.TASK_URL):
                    rel_path = task.url[len(settings.TASK_URL):].lstrip("/")
                    file_path = os.path.join(settings.TASK_ROOT, rel_path)

            # 删除任务
            task.delete()

            # 删除附件文件
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print("[delete_course_task] file delete error:", e)

        return JsonResponse({"success": True})

    except Exception as e:
        print("[delete_course_task] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
@csrf_exempt
def update_course_task(request, course_id: str, task_id: int):
    if request.method not in ("PUT", "POST", "PATCH"):
        return err("Method not allowed", status=405)

    # 解析 JSON
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return err("invalid json body")

    # 查任务（限定 course_id）
    task = CourseTask.objects.filter(id=task_id, course_code=course_id).first()
    if not task:
        return err("Task not found", status=404)

    # 取字段（仅对提供的字段做更新）
    title = body.get("title", None)
    deadline_raw = body.get("deadline", None)
    brief = body.get("brief", None)
    pc_raw = body.get("percent_contribution", None)
    new_url = body.get("url", None)  # 只有传了才表示要覆盖

    # 校验（仅对传入的字段）
    if title is not None:
        if not str(title).strip():
            return err("title cannot be empty")

    if deadline_raw is not None:
        dl = parse_date(str(deadline_raw))
        if not dl:
            return err("deadline must be YYYY-MM-DD")
        # 不允许过去日期（允许今天）
        if dl < date.today():
            return err("deadline cannot be in the past")
    else:
        dl = None

    if pc_raw is not None:
        try:
            pc = int(pc_raw)
        except Exception:
            return err("percent_contribution must be an integer")
        if pc < 0 or pc > 100:
            return err("percent_contribution must be in [0,100]")
    else:
        pc = None

    # 是否删除旧文件：仅当传了新 url 且参数要求删除时有效
    delete_old = request.GET.get("delete_old_file") in ("1", "true", "True")

    # 记录旧 url（用于可能的文件删除）
    old_url = task.url

    # 执行更新
    try:
        with transaction.atomic():
            if title is not None:
                task.title = str(title).strip()
            if dl is not None:
                task.deadline = dl
            if brief is not None:
                task.brief = str(brief).strip()
            if pc is not None:
                task.percent_contribution = pc
            if new_url is not None:
                task.url = new_url  # 用新附件覆盖

            task.save()

        # 保存成功后，再按需删除旧文件
        if new_url is not None and delete_old and old_url and old_url != new_url:
            # 仅允许删除 TASK_URL 命名空间内的文件
            if hasattr(settings, "TASK_URL") and hasattr(settings, "TASK_ROOT"):
                if str(old_url).startswith(settings.TASK_URL):
                    rel_path = str(old_url)[len(settings.TASK_URL):].lstrip("/\\")
                    file_path = os.path.join(settings.TASK_ROOT, rel_path)
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        # 不抛错以免影响业务；可在此记录日志
                        print("[update_course_task] remove old file error:", e)

        return ok(None)
    except Exception as e:
        print("[update_course_task] error:", e)
        return err(str(e), status=500)

@csrf_exempt
def create_course_materials(request, course_id: str):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

    title = (payload.get("title") or "").strip()
    url = (payload.get("url") or "").strip()
    description = (payload.get("description") or "").strip()

    if not title:
        return JsonResponse({"success": False, "message": "title is required"}, status=400)
    if not url:
        return JsonResponse({"success": False, "message": "url is required"}, status=400)
    if not course_id:
        return JsonResponse({"success": False, "message": "course_id is required"}, status=400)

    try:
        material = Material.objects.create(
            course_code=course_id,
            title=title,
            description=description,
            url=url,
        )
        return JsonResponse({"success": True, "data": {"id": material.id}})
    except Exception as e:
        print("[create_course_materials] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def upload_material_file(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "file is required"}, status=400)

    #  从表单取课程 ID，用于保存路径
    course_id = (request.POST.get("course") or "").strip()
    if not course_id:
        return JsonResponse({"error": "course id is required"}, status=400)

    # 拼接保存目录 material/<course_id>/
    subdir = os.path.join(course_id)
    save_dir = os.path.join(settings.MAT_ROOT, subdir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f.name
    save_path = os.path.join(save_dir, filename)

    # 保存文件
    with open(save_path, "wb+") as dst:
        for chunk in f.chunks():
            dst.write(chunk)

    url_path = f"{settings.MAT_URL}{course_id}/{filename}".replace("\\", "/")

    return JsonResponse({
        "success": True,
        "data": {
            "url": url_path,
            "filename": filename,
            "size": f.size,
        }
    })

@csrf_exempt
def delete_course_material(request, course_id: str, materials_id: int):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    try:
        # 1) 读取记录并校验课程归属
        try:
            material = Material.objects.get(id=materials_id, course_code=course_id)
        except Material.DoesNotExist:
            return JsonResponse({"success": False, "message": "material not found"}, status=404)

        # 2) 从 url 还原文件名并构造磁盘路径
        url_value = (material.url or "").strip()
        # 防 URL 编码（空格/中文）
        url_value = unquote(url_value)

        filename = os.path.basename(url_value)  # 只取文件名
        course_dir = os.path.join(settings.MAT_ROOT, course_id)
        file_path = os.path.join(course_dir, filename)

        # 安全删除文件（文件不存在则忽略）
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as fe:
            # 记录日志但不阻塞删除 DB
            print(f"[delete_course_material] remove file failed: {file_path} err={fe}")

        # 3) 删除数据库记录
        material.delete()

        return JsonResponse({"success": True})
    except Exception as e:
        print("[delete_course_material] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
@csrf_exempt
def update_course_material(request, course_id: str, materials: int):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    # 解析 JSON
    try:
      payload = json.loads(request.body.decode("utf-8"))
    except Exception:
      return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

    title = (payload.get("title") or "").trim() if hasattr(str, 'trim') else (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    new_url = (payload.get("url") or "").strip()

    if not title:
        return JsonResponse({"success": False, "message": "title is required"}, status=400)

    try:
        material = Material.objects.get(id=materials, course_code=course_id)

        # 如果提供了新的 URL，且与旧 URL 不同，则尝试删除旧文件
        old_url = (material.url or "").strip()
        if new_url and old_url and new_url != old_url:
            try:
                
                old_url_decoded = unquote(old_url)
                old_filename = os.path.basename(old_url_decoded)
                old_path = os.path.join(settings.MAT_ROOT, course_id, old_filename)
                if os.path.isfile(old_path):
                    os.remove(old_path)
            except Exception as fe:
              
                print(f"[update_course_material] remove old file failed: {old_path if 'old_path' in locals() else ''} err={fe}")

        # 更新字段
        material.title = title
        material.description = description
        if new_url:
            material.url = new_url
        material.save()

        return JsonResponse({"success": True})
    except Material.DoesNotExist:
        return JsonResponse({"success": False, "message": "material not found"}, status=404)
    except Exception as e:
        print("[update_course_material] error:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
    



import os
import urllib.parse
from django.http import FileResponse, JsonResponse
from django.conf import settings
from django.utils.encoding import escape_uri_path
##下载material
def download_material(request, filename):
    decoded_name = urllib.parse.unquote(filename).strip()
    print(f"[DEBUG] Looking for file: '{decoded_name}' in {settings.MAT_ROOT}")

    try:
        for root, _, files in os.walk(settings.MAT_ROOT):
            for f in files:
                name_without_ext, ext = os.path.splitext(f)
                if decoded_name == f or decoded_name == name_without_ext:
                    file_path = os.path.join(root, f)
                    print(f"[download_material] Serving file: {file_path}")
                    response = FileResponse(open(file_path, "rb"), as_attachment=True)
                    safe_name = escape_uri_path(f)
                    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{safe_name}"

                    return response

        print(f"[download_material] error: file not found ({decoded_name})")
        return JsonResponse({"success": False, "message": "File not found"}, status=404)

    except Exception as e:
        print(f"[download_material] error: {e}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)
