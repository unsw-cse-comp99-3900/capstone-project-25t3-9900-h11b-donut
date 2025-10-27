from stu_accounts.models import StudentAccount
from django.http import HttpRequest
from typing import Optional
import secrets

def make_token() -> str:
    #payload = json.dumps({"student_id": student_id}).encode("utf-8")
    #return base64.urlsafe_b64encode(payload).decode("utf-8")
    return secrets.token_urlsafe(48)
def get_student_id_from_request(request: HttpRequest) -> Optional[str]:
    """
    从 Authorization: Bearer <token> 头部解析并反查当前 student_id。
    新实现：直接查询数据库的 current_token，不再解码 token。
    """
   
    auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
    if not auth.startswith("Bearer "):
        return None

    token = auth[7:].strip()
    if not token:
        return None

    # 从数据库反查 token 对应的用户
    account = (
        StudentAccount.objects
        .only("student_id")
        .filter(current_token=token)
        .first()
    )
    return account.student_id if account else None