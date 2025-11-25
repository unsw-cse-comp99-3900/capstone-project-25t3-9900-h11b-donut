from django.db import IntegrityError
import bcrypt
from .models import StudentAccount 
from django.conf import settings
from django.http import JsonResponse, HttpRequest
import json
from django.views.decorators.http import require_POST
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
from decimal import Decimal
from reminder.models import Notification


ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB

def api_ok(data=None, message="OK", status=200):
    return JsonResponse({"success": True, "message": message, "data": data}, status=status)

def api_err(message="Bad Request", status=400):
    return JsonResponse({"success": False, "message": message, "data": None}, status=status)

def _json_body(request: HttpRequest):
    """decode the request"""
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}

@csrf_exempt
def register_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        # --- 1)  JSON and FormData ---
        content_type = (request.META.get("CONTENT_TYPE") or "").lower()

        if content_type.startswith("application/json"):
            # pure JSON
            data = json.loads(request.body.decode("utf-8") or "{}")
            student_id = (data.get("student_id") or "").strip()
            email = (data.get("email") or "").strip()
            name = (data.get("name") or "").strip() 
            password = data.get("password") or ""
            avatar_file = None
        else:
            # FormData（multipart）：txt-> POST ，file -> FILES 
            student_id = (request.POST.get("student_id") or "").strip()
            email = (request.POST.get("email") or "").strip()
            name = (request.POST.get("name") or "").strip()  
            password = request.POST.get("password") or ""
            avatar_file = request.FILES.get("avatar")

        if not student_id or not email or not password or not name:
            return JsonResponse({"success": False, "message": "Please enter zid, email and password"}, status=400)
        try:
            validate_id(student_id)                  
            validate_email(email)                              
            validate_name(name)                                
            validate_password(password, student_id=student_id, email=email)  
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)
        
        # --- 2) duplicate check
        if StudentAccount.objects.filter(student_id=student_id).exists():
            return JsonResponse({"success": False, "message": "Student ID already exists"}, status=409)
        if StudentAccount.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "Email already exists"}, status=409)

        # --- 3) handle avatar
        avatar_url = None
        if avatar_file:
            
            if avatar_file.size > MAX_AVATAR_BYTES:
                return JsonResponse({"success": False, "message": "Avatar too large (max 2MB)"}, status=400)

           
            ext = os.path.splitext(avatar_file.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                return JsonResponse({"success": False, "message": "Only .jpg/.jpeg/.png allowed"}, status=400)

            #save to folder
            student_dir = os.path.join(settings.MEDIA_ROOT, student_id)
            os.makedirs(student_dir, exist_ok=True)

            filename = f"{student_id}_{get_random_string(8)}{ext}"
            save_path = os.path.join(student_dir, filename)

            with open(save_path, "wb") as f:
                for chunk in avatar_file.chunks():
                    f.write(chunk)

            # reply with URL：/media/<student_id>/<file_name>
            avatar_url = f"{settings.MEDIA_URL}{student_id}/{filename}"

        # --- 4) write into db
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        create_kwargs = dict(
            student_id=student_id,
            email=email,
            name=name,
            password_hash=hashed,
        )
       
        if hasattr(StudentAccount, "avatar_url"):
            create_kwargs["avatar_url"] = avatar_url or ""

        StudentAccount.objects.create(**create_kwargs)

        # --- 5) return ---
        return JsonResponse({
            "success": True,
            "message": "Registered successfully",
            "data": {
                "student_id": student_id,
                "email": email,
                "name": name, 
                "avatar_url": avatar_url,  
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
            .only("student_id", "email", "name", "password_hash", "avatar_url", "bonus") 
            # less IO
            .get(student_id=student_id)
        )
        ok = bcrypt.checkpw(password.encode("utf-8"), account.password_hash.encode("utf-8"))
        if not ok:
            return api_err("Invalid id or password", 401)

        token = make_token()
        
        now = timezone.now()
        with transaction.atomic():
            account.current_token = token
            account.token_issued_at = now
            account.save(update_fields=["current_token", "token_issued_at"])

        user_payload = {
            "studentId": account.student_id,
            "name": account.name or "",
            "email": account.email or "",
            "avatarUrl": getattr(account, "avatar_url", None),  
            "bonus": str(account.bonus or Decimal("0")), 
        }

        return api_ok({"token": token, "user": user_payload})

    except Exception as e:
        print("[API LOGIN ERROR]", repr(e))
        return api_err("Server Error", 500)


@csrf_exempt
def logout_api(request: HttpRequest):
    
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed", "data": None}, status=405)
    
    # clear session
    request.session.flush()
    return JsonResponse({"success": True, "message": "Logged out successfully", "data": None})

@csrf_exempt
@require_POST
def add_bonus_api(request):
    print(">>> ADD BONUS API CALLED !!!", flush=True)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}

    raw_delta = body.get('delta', 0.1)
    try:
        delta = Decimal(str(raw_delta))
    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Invalid delta",
        }, status=400)

    account = getattr(request, "account", None)
    if not isinstance(account, StudentAccount):
        return JsonResponse({
            "success": False,
            "message": "Not authenticated as student",
        }, status=401)

    student: StudentAccount = account
    max_bonus = Decimal("2.0")
    current_bonus = student.bonus or Decimal("0")

    if current_bonus >= max_bonus:
        return JsonResponse({
            "success": True,
            "data": {
                "bonus": str(current_bonus),
            },
            "message": "MAX_BONUS_REACHED",
        })
    # update bonus
    new_bonus = current_bonus + delta
    if new_bonus > max_bonus:
        new_bonus = max_bonus

    student.bonus = new_bonus
    student.save(update_fields=["bonus"])

    #  create Notification 
    try:
        from reminder.models import Notification
        n = Notification.objects.create(
            student_id=student.student_id,
            message_type="bonus",
            title="Bonus Earned!",
            preview=f"You received a bonus of {delta}",
            content=f"Your bonus increased to {new_bonus}",
        )
        print(f">>> [DEBUG] Notification created! ID={n.id}", flush=True)
    except Exception as e:
        print(f">>> [DEBUG] Notification creation FAILED: {e}", flush=True)


    return JsonResponse({
        "success": True,
        "data": {
            "bonus": str(student.bonus),
        },
    })


@csrf_exempt
@require_POST
def reset_bonus_api(request):
    
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return JsonResponse(
            {"success": False, "message": "Unauthorized", "data": None},
            status=401,
        )

    token = auth.split(" ", 1)[1].strip()
    if not token:
        return JsonResponse(
            {"success": False, "message": "Unauthorized", "data": None},
            status=401,
        )

    try:
        stu = StudentAccount.objects.get(current_token=token)
    except StudentAccount.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Unauthorized", "data": None},
            status=401,
        )

    stu.bonus = Decimal("0.00")
    stu.save(update_fields=["bonus"])

    return JsonResponse(
        {
            "success": True,
            "message": "Bonus reset",
            "data": {
                "student_id": stu.student_id,
                "bonus": "0.00",
            },
        }
    )



















