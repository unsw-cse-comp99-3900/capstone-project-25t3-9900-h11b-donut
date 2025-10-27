import bcrypt, os, json
from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from .models import AdminAccount
from utils.validators import validate_email, validate_id, validate_name, validate_password

# 头像配置
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB

def api_ok(data=None, message="OK", status=200):
    return JsonResponse({"success": True, "message": message, "data": data}, status=status)

def api_err(message="Bad Request", status=400):
    return JsonResponse({"success": False, "message": message, "data": None}, status=status)

@csrf_exempt
def register_admin(request: HttpRequest):
    """管理员注册接口"""
    
    if request.method != "POST":
        return api_err("Method Not Allowed", 405)

    try:
        # --- 1) 同时兼容 JSON 与 FormData ---
        if (request.content_type or "").lower().startswith("application/json"):
            data = json.loads(request.body.decode("utf-8") or "{}")
            admin_id = (data.get("admin_id") or "").strip()
            email = (data.get("email") or "").strip().lower()
            full_name = (data.get("fullName") or "").strip()
            password = data.get("password") or ""
            avatar_file = None
        else:
            admin_id = (request.POST.get("admin_id") or "").strip()
            email = (request.POST.get("email") or "").strip().lower()
            full_name = (request.POST.get("fullName") or "").strip()
            password = request.POST.get("password") or ""
            avatar_file = request.FILES.get("avatar")

        # --- 2) 基础校验 ---
        if not admin_id or not email or not password or not full_name:
            return api_err("Please enter admin_id, email, name and password", 400)

        try:
            validate_id(admin_id)
            validate_email(email)
            validate_name(full_name)
            validate_password(password, student_id=admin_id, email=email)
        except ValidationError as ve:
            return api_err(str(ve), 400)

        # --- 3) 查重 ---
        if AdminAccount.objects.filter(admin_id=admin_id).exists():
            return api_err("Admin ID already exists", 409)
        if AdminAccount.objects.filter(email=email).exists():
            return api_err("Email already exists", 409)

        # --- 4) 处理头像 ---
        avatar_url = None
        if avatar_file:
            if avatar_file.size > MAX_AVATAR_BYTES:
                return api_err("Avatar too large (max 2MB)", 400)

            ext = os.path.splitext(avatar_file.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                return api_err("Only .jpg/.jpeg/.png allowed", 400)

            safe_name = os.path.basename(avatar_file.name)
            rel_path = f"avatars/{admin_id}/{admin_id}_{safe_name}"

            saved_path = default_storage.save(rel_path, ContentFile(avatar_file.read()))
            base = getattr(settings, "MEDIA_URL", "/media/")
            avatar_url = f"{base}{saved_path}"

        # --- 5) 哈希密码 + 写入数据库 ---
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with transaction.atomic():
            AdminAccount.objects.create(
                admin_id=admin_id,
                email=email,
                full_name=full_name,
                password_hash=hashed,
                avatar_url=avatar_url,
            )

        # --- 6) 返回成功信息 ---
        return JsonResponse({
            "success": True,
            "message": "Admin registered successfully",
            "data": {
                "admin_id": admin_id,
                "email": email,
                "full_name": full_name,
                "avatar_url": avatar_url,
            }
        }, status=201)

    except IntegrityError:
        return api_err("Admin ID or email already exists", 409)
    except Exception as e:
        print("[ADMIN REGISTER ERROR]", repr(e))
        return api_err("Internal server error", 500)
