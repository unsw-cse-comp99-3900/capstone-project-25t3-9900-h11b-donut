import base64, json
from django.http import HttpRequest
def make_token(student_id: str) -> str:
    # 把学号放到一个简单的 base64 token 里（示范用，后期可换成 JWT）
    payload = json.dumps({"student_id": student_id}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")
def get_student_id_from_request(request: HttpRequest) -> str | None: #解析学号
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.removeprefix("Bearer ").strip()
    try:
        data = json.loads(base64.urlsafe_b64decode(token))
        return data.get("student_id")
    except Exception:
        return None