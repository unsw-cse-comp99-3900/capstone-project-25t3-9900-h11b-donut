# middleware/auth_token.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from stu_accounts.models import StudentAccount
from adm_accounts.models import AdminAccount

class AuthTokenMiddleware(MiddlewareMixin):
    # 登录、注册等公共接口
    PUBLIC_PREFIXES = (
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/register",   
        "/api/admin/register",
        "/api/admin/login",
    )

    # ✅ 新增：静态文件白名单路径
    PUBLIC_FILE_PREFIXES = (
        "/task/",
        "/api/task/",
        "/material/",
        "/api/material/",
        "/media/",
        "/api/media/",
    )

    def process_request(self, request):
        path = request.path

        # ✅ 如果是静态文件路径，直接放行，不要求 token
        if any(path.startswith(p) for p in self.PUBLIC_FILE_PREFIXES):
            return None

        # ✅ 原本就有的登录注册白名单
        if any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return None  

        # 读取 Bearer token
        auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
        if not auth.startswith("Bearer "):
            return JsonResponse({
                "success": False,
                "code": "UNAUTHORIZED",
                "message": "Missing token",
                "data": None
            }, status=401)

        token = auth[7:].strip()
        if not token:
            return JsonResponse({
                "success": False,
                "code": "UNAUTHORIZED",
                "message": "Empty token",
                "data": None
            }, status=401)

        # 用 current_token 反查用户
        account = StudentAccount.objects.filter(current_token=token).only(
            "student_id", "name", "email", "avatar_url"
        ).first()
        if not account:
            account = AdminAccount.objects.filter(current_token=token).only(
                "admin_id", "full_name", "email", "avatar_url"
            ).first()
        
        if not account:
            return JsonResponse({
                "success": False,
                "code": "KICKED",
                "message": "Logged in elsewhere",
                "data": None
            }, status=401)

        # 通过，挂在 request 上
        request.account = account
        return None
