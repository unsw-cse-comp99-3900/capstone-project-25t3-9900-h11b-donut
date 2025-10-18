export const EMAIL_RE = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
export const STUDENT_ID_RE = /^[zZ]\d{7}$/;       
export const NAME_RE = /^[A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u2E80-\u9FFF·'\- ]{2,50}$/;
export const PASSWORD_STRICT_RE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s])\S{8,64}$/;

export function validateEmail(v: string) {
  return EMAIL_RE.test((v || '').trim());
}
export function validateStudentId(v: string) {
  return STUDENT_ID_RE.test((v || '').trim());
}
export function validateName(v: string) {
  return NAME_RE.test((v || '').trim());
}
export function validatePassword(v: string, studentId?: string, email?: string) {
  const pass = PASSWORD_STRICT_RE.test(v || '');
  if (!pass) return false;
  const local = (email || '').split('@')[0];
  const low = (v || '').toLowerCase();
  if (studentId && low.includes(studentId.toLowerCase())) return false;
  if (local && low.includes(local.toLowerCase())) return false;
  return true;
}
