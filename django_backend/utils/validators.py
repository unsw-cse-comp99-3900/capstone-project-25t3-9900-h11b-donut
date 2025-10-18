# accounts/validators.py
import re
from django.core.exceptions import ValidationError

EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
STUDENT_ID_RE = re.compile(r'^[zZ]\d{7}$')  # 如果你学校不是 z+7位，改这里
NAME_RE = re.compile(r"^[A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u2E80-\u9FFF·'\- ]{2,50}$")
PASSWORD_STRICT_RE = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s])\S{8,64}$')

def validate_email(value: str):
    if not EMAIL_RE.match((value or "").strip()):
        raise ValidationError("Wrong Email Format")

def validate_student_id(value: str):
    if not STUDENT_ID_RE.match((value or "").strip()):
        raise ValidationError("Wrong ID Format(eg:z1234567)")

def validate_name(value: str):
    v = (value or "").strip()
    if not NAME_RE.match(v):
        raise ValidationError("Names are only allowed in letters")

def validate_password(value: str, *, student_id: str = "", email: str = ""):
    v = value or ""
    if not PASSWORD_STRICT_RE.match(v):
        raise ValidationError("The password needs to be 8-64 characters long, including at least one uppercase and lowercase letter, one numeric character, and one special character")
    local = (email or "").split("@")[0]
    for s in (student_id or "", local or ""):
        s = s.strip()
        if s and s.lower() in v.lower():
            raise ValidationError("cannot include the student ID/email prefix!")
