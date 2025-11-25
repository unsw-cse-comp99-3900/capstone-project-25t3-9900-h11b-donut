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
    Parse from the Authorization: Bearer<token>header and backtrack the current student ID.
New implementation: Directly query the database's current token without decoding the token.
    """
   
    auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
    if not auth.startswith("Bearer "):
        return None

    token = auth[7:].strip()
    if not token:
        return None

    # Retrieve the user corresponding to the token from the database
    account = (
        StudentAccount.objects
        .only("student_id")
        .filter(current_token=token)
        .first()
    )
    return account.student_id if account else None