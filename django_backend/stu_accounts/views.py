from django.db import IntegrityError
import bcrypt
from .models import StudentAccount 
from django.conf import settings
from django.http import JsonResponse, HttpRequest
import json
from django.views.decorators.csrf import csrf_exempt
import os
from django.db import transaction                         
from django.utils import timezone    
from django.utils.crypto import get_random_string
from utils.auth import make_token
from utils.validators import (
    validate_email, validate_id, validate_name, validate_password
)
from django.core.exceptions import ValidationError


ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB

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
        # --- 1) 同时兼容 JSON 与 FormData ---
        content_type = (request.META.get("CONTENT_TYPE") or "").lower()

        if content_type.startswith("application/json"):
            # 纯 JSON：不支持文件
            data = json.loads(request.body.decode("utf-8") or "{}")
            student_id = (data.get("student_id") or "").strip()
            email = (data.get("email") or "").strip()
            name = (data.get("name") or "").strip() 
            password = data.get("password") or ""
            avatar_file = None
        else:
            # FormData（multipart）：文本从 POST 取，文件从 FILES 取
            student_id = (request.POST.get("student_id") or "").strip()
            email = (request.POST.get("email") or "").strip()
            name = (request.POST.get("name") or "").strip()  
            password = request.POST.get("password") or ""
            avatar_file = request.FILES.get("avatar")

        if not student_id or not email or not password or not name:
            return JsonResponse({"success": False, "message": "Please enter zid, email and password"}, status=400)
        try:
            validate_id(student_id)                    # 学号：如 z1234567
            validate_email(email)                              # 邮箱基本格式
            validate_name(name)                                # 姓名：中/英、空格、-、·、’ 2~50
            validate_password(password, student_id=student_id, email=email)  # 密码强度+不含学号/邮箱前缀
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)
        
        # --- 2) 重复检查（更友好地返回409） ---
        if StudentAccount.objects.filter(student_id=student_id).exists():
            return JsonResponse({"success": False, "message": "Student ID already exists"}, status=409)
        if StudentAccount.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "Email already exists"}, status=409)

        # --- 3) 处理头像（可选，仅当是 FormData 且有文件） ---
        avatar_url = None
        if avatar_file:
            # 大小校验
            if avatar_file.size > MAX_AVATAR_BYTES:
                return JsonResponse({"success": False, "message": "Avatar too large (max 2MB)"}, status=400)

            # 后缀校验
            ext = os.path.splitext(avatar_file.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                return JsonResponse({"success": False, "message": "Only .jpg/.jpeg/.png allowed"}, status=400)

            # 保存到 media/<student_id>/ 目录
            student_dir = os.path.join(settings.MEDIA_ROOT, student_id)
            os.makedirs(student_dir, exist_ok=True)

            filename = f"{student_id}_{get_random_string(8)}{ext}"
            save_path = os.path.join(student_dir, filename)

            with open(save_path, "wb") as f:
                for chunk in avatar_file.chunks():
                    f.write(chunk)

            # 返回给前端的访问URL：/media/<student_id>/<文件名>
            avatar_url = f"{settings.MEDIA_URL}{student_id}/{filename}"

        # --- 4) 写入数据库（哈希密码 + 可选 avatar_url） ---
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        create_kwargs = dict(
            student_id=student_id,
            email=email,
            name=name,
            password_hash=hashed,
        )
       
        if hasattr(StudentAccount, "avatar_url"):
            create_kwargs["avatar_url"] = avatar_url

        StudentAccount.objects.create(**create_kwargs)

        # --- 5) 返回 ---
        return JsonResponse({
            "success": True,
            "message": "Registered successfully",
            "data": {
                "student_id": student_id,
                "email": email,
                "name": name, 
                "avatar_url": avatar_url,  # 前端可直接显示；如果没上传则为 None
            }
        }, status=201)

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
    student_id = (body.get("student_id") or "").strip()
    password = body.get("password") or ""

    if not student_id or not password:
        return api_err("id and password are required")

    try:
        
        account = (
            StudentAccount.objects
            .only("student_id", "email", "name", "password_hash", "avatar_url")  # 提前限定字段，减少 IO
            .get(student_id=student_id)
        )
        ok = bcrypt.checkpw(password.encode("utf-8"), account.password_hash.encode("utf-8"))
        if not ok:
            return api_err("Invalid id or password", 401)

        token = make_token()
        # 在 user 里带上 avatarUrl
        now = timezone.now()
        with transaction.atomic():
            account.current_token = token
            account.token_issued_at = now
            # 如果你有 last_login_at 等字段，也可以一并更新
            account.save(update_fields=["current_token", "token_issued_at"])

        user_payload = {
            "studentId": account.student_id,
            "name": account.name or "",
            "email": account.email or "",
            "avatarUrl": getattr(account, "avatar_url", None),  # 可能为 None
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


























