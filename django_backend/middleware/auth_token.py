# middleware/auth_token.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from stu_accounts.models import StudentAccount
from adm_accounts.models import AdminAccount

class AuthTokenMiddleware(MiddlewareMixin):
    # for route_protection
    PUBLIC_PREFIXES = (
        "/api/login",
        "/api/logout",
        "/api/register",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/register",   
        "/api/admin/register",
        "/api/admin/login",
        "/api/ai/health/",  
        "/api/ai/chat/",  
        "/api/ai/generate-practice/",  
        "/api/ai/questions/generate",  
        "/api/ai/questions/session/", 
        "/api/ai/answers/submit",  
        "/api/overdue/report-day", 
    )

    # whitelist
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

        # If it is a static file path, it can be released directly without requiring a token
        if any(path.startswith(p) for p in self.PUBLIC_FILE_PREFIXES):
            return None

        # The existing login and registration whitelist
        if any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return None  

        # read Bearer token
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

        # Use Current_token to backtrack users
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

        request.account = account
        return None
