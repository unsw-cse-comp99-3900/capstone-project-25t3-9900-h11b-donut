# middleware/auth_token.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from accounts.models import StudentAccount

class AuthTokenMiddleware(MiddlewareMixin):
    PUBLIC_PREFIXES = (
        "/api/auth/login",
        "/api/auth/register",   
    )

    def process_request(self, request):
        path = request.path
        if any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return None  # 这些路由不鉴权

        # 读取 Bearer token（兼容某些环境）
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

        # 鉴权通过，挂在 request 上
        request.account = account
        return None
