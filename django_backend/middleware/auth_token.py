# middleware/auth_token.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from stu_accounts.models import StudentAccount

class AuthTokenMiddleware(MiddlewareMixin):
    PUBLIC_PREFIXES = (
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/register",   
        "/api/admin/register",
    )

    def process_request(self, request):
        path = request.path
        if any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return None  

        # 读取 Bearer token
        auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
        if not auth.startswith("Bearer "):
            return JsonResponse({"success": False, "code": "UNAUTHORIZED", "message": "Missing token", "data": None}, status=401)

        token = auth[7:].strip()
        if not token:
            return JsonResponse({"success": False, "code": "UNAUTHORIZED", "message": "Empty token", "data": None}, status=401)

        # 用 current_token 反查用户
        account = StudentAccount.objects.filter(current_token=token).only("student_id", "name", "email", "avatar_url").first()
        if not account:
            return JsonResponse({"success": False, "code": "KICKED", "message": "Logged in elsewhere", "data": None}, status=401)

        # 通过，挂在 request 上
        request.account = account
        return None
