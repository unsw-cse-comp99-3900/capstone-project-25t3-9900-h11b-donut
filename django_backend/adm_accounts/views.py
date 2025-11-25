import bcrypt, os, json
from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone   
from .models import AdminAccount 
from utils.validators import validate_email, validate_id, validate_name, validate_password
from utils.auth import make_token
# avatar configure
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB

def api_ok(data=None, message="OK", status=200):
    return JsonResponse({"success": True, "message": message, "data": data}, status=status)

def api_err(message="Bad Request", status=400):
    return JsonResponse({"success": False, "message": message, "data": None}, status=status)
def _json_body(request: HttpRequest):
   
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}
@csrf_exempt
def register_admin(request: HttpRequest):
   
    
    if request.method != "POST":
        return api_err("Method Not Allowed", 405)

    try:
        # --- 1) JSON  FormData acceptable ---
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

        # --- 2) basic check---
        if not admin_id or not email or not password or not full_name:
            return api_err("Please enter admin_id, email, name and password", 400)

        try:
            validate_id(admin_id)
            validate_email(email)
            validate_name(full_name)
            validate_password(password, student_id=admin_id, email=email)
        except ValidationError as ve:
            return api_err(str(ve), 400)

        # --- 3) duplicate check ---
        if AdminAccount.objects.filter(admin_id=admin_id).exists():
            return api_err("Admin ID already exists", 409)
        if AdminAccount.objects.filter(email=email).exists():
            return api_err("Email already exists", 409)

        # --- 4) handle avatar ---
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

        # --- 5) use hash pwd and store into db ---
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with transaction.atomic():
            AdminAccount.objects.create(
                admin_id=admin_id,
                email=email,
                full_name=full_name,
                password_hash=hashed,
                avatar_url=avatar_url,
            )

        # --- 6) return msg ---
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
    
@csrf_exempt
def login_admin(request: HttpRequest):
    if request.method != "POST":
        return api_err("Method Not Allowed", 405)
    body = _json_body(request)
    print(body)
    admin_id = (body.get("admin_id") or "").strip()
    password = body.get("password") or ""
    if not admin_id or not password:
            return api_err("admin_id and password are required", 400)
    
    try:
        account = (
            AdminAccount.objects
            .only("admin_id", "email", "full_name", "password_hash", "avatar_url")  
            .get(admin_id=admin_id)
        )
        ok = bcrypt.checkpw(password.encode("utf-8"), account.password_hash.encode("utf-8"))
        if not ok:
            return api_err("Invalid id or password", 401)

        token = make_token()
        # user with avatarUrl
        now = timezone.now()
        with transaction.atomic():
            account.current_token = token
            account.token_issued_at = now
            account.save(update_fields=["current_token", "token_issued_at"])

        user_payload = {
            "adminId": account.admin_id,
            "name": account.full_name or "",
            "email": account.email or "",
            "avatarUrl": getattr(account, "avatar_url", None),  # possible None
        }

        return api_ok({"token": token, "user": user_payload})

    except Exception as e:
        print("[API LOGIN ERROR]", repr(e))
        return api_err("Server Error", 500)
    
@csrf_exempt
def logout_admin(request: HttpRequest):
    
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed", "data": None}, status=405)
    
    # 清空 session
    request.session.flush()
    return JsonResponse({"success": True, "message": "Logged out successfully", "data": None})