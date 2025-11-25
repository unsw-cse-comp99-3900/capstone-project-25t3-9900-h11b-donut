// API Service Layer - Backend Integration Interface
import type { WeeklyPlan } from '../store/preferencesStore';
import {
  validateEmail, validateId, validateName, validatePassword
} from '../components/validators';
import type { Message } from '../types/message';
const API_BASE = '/api';

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiCourse {
  id: string;
  title: string;
  description: string;
  illustration: 'orange' | 'student' | 'admin';
}

export interface ApiTask {
  id: string;
  title: string;
  deadline: string;
  brief?: string;
  percentContribution?: number;
  url?: string | null
}
export interface CreateTaskPayload {
  title: string;
  deadline: string;                  
  brief?: string;
  percent_contribution: number;     
  url?: string | null;                
}
export interface ApiMaterial {
  id: number | string;
  course_code: string;
  title: string;
  url: string;
  description?: string;
}
export interface ApiQuestionChoice {
  label?: string | null;
  order: number;
  content: string;
  isCorrect: boolean;
}
export interface ApiQuestion {
  id?: number | string;
  qtype: 'mcq' | 'short';
  title: string;
  description: string;
  text: string;
  keywords: string[];
  // mcq
  choices?: ApiQuestionChoice[];
  // short
  answer?: string;
}
export interface ApiPreferences {
  dailyHours: number;
  weeklyStudyDays: number;
  avoidDays: string[];
  saveAsDefault: boolean;
  description?: string;
}

export interface ApiPlanItem {
  id: string;
  courseId: string;
  courseTitle: string;
  partTitle: string;
  minutes: number;
  date: string;
  color: string;
  completed?: boolean;
  partIndex?: number;
  partsCount?: number;
}

class ApiService {
  private token: string | null = (typeof window !== 'undefined'
    ? localStorage.getItem('auth_token')
    : null);;

  public async get<T>(endpoint: string, params?: Record<string, string | number>): Promise<ApiResponse<T>> {
    // Build query parameters
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        queryParams.append(key, value.toString());
      });
    }
    
    const url = queryParams.toString() 
      ? `${endpoint}?${queryParams.toString()}`
      : endpoint;
      
    return this.request<T>(url, { method: 'GET' });
  }

  public async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined
    });
  }

  protected async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${endpoint}`;

  const headers = new Headers(options.headers as HeadersInit | undefined);
 
  // Token: Prioritize this.token, if not available, retrieve from localStorage
  let token = this.token;
  if (!token) {
    try { token = localStorage.getItem('auth_token') || ''; } catch { token = ''; }
    if (token) this.token = token;
  }

  // Unified supplementary authentication header
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Set Content Type conditionally based on body type
  const body = options.body as any;
  if (body === undefined || body === null) {
    headers.delete('Content-Type');
  } else if (body instanceof FormData || body instanceof Blob || body instanceof File) {
    headers.delete('Content-Type');
  } else if (typeof body === 'string') {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
  } else {
  }

  const config: RequestInit = {
    ...options,
    headers,                 
  };

  try {
    const response = await fetch(url, config);
    const text = await response.text();
    let payload: ApiResponse<T> | null = null;
    try { payload = text ? JSON.parse(text) : null; } catch { payload = null; }

    //  Unified interception of 401 (not logged in/expired/squeezed offline)
    if (response.status === 401) {
      const code = (payload as any)?.code || 'UNAUTHORIZED';

      try {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        localStorage.removeItem('current_user_id');
      } catch {}

      // If squeezed offline, give a prompt
      if (code === 'KICKED') {
        try { alert('你的账号在另一处登录，你已下线'); } catch {}
      }


      try { window.location.href = '#/login'; } catch {}


      return { success: false, message: 'Unauthorized', data: null as unknown as T };
    }

 
    if (payload && typeof (payload as any).success === 'boolean') {
      return payload as ApiResponse<T>;
    }

  
    return {
      success: response.ok,
      message: response.ok ? 'OK' : `HTTP ${response.status}`,
      data: null as unknown as T,
    };
  } catch (error) {
    console.error('API request failed:', error);
    throw error; 
  }
}

  async searchCourses(q: string): Promise<ApiCourse[]> {
    const res = await this.request<ApiCourse[]>('/courses/search?q=' + encodeURIComponent(q));
    // return  {code,title,description,illustration} from backend
    const raw = (res.data ?? []) as any[];
    return raw.map(r => ({
      id: r.code,
      title: r.title,
      description: r.description,
      illustration: r.illustration as 'orange'|'student'|'admin',
    }));
  }
  // user validate
  async stu_register(student_id: string, name: string,email: string, password: string, avatarFile?: File) {
    if (!validateId(student_id)) {
    throw new Error("Wrong ID Format(eg:z1234567)");
  }
  if (!validateEmail(email)) {
    throw new Error("Wrong Email Format");
  }
  if (!validateName(name)) {
    throw new Error("Names are only allowed in letters");
  }
  if (!validatePassword(password, student_id, email)) {
    throw new Error(
      "The password needs to be 8-64 characters long, including at least one uppercase and lowercase letter, one numeric character, and one special character, and does not include the student ID/email prefix"
    );
  }
  const formData = new FormData();
  formData.append("student_id", student_id);
  formData.append("email", email);
  formData.append("name", name);     
  formData.append("password", password);
  if (avatarFile) {
    formData.append("avatar", avatarFile); // backend: request.FILES.get("avatar")
  }

  const result = await this.request<ApiResponse<any>>("/auth/register", {
    method: "POST",
    body: formData,
  });

  if (!result.success) {
    throw new Error(result.message || "fail to register");
  }
  return result;
}

async adm_register(admin_id: string, fullName: string, email: string, password: string, avatarFile?: File) {
  if (!validateId(admin_id)) throw new Error("Wrong ID Format(eg:z1234567)");
  if (!validateEmail(email)) throw new Error("Wrong Email Format");
  if (!validateName(fullName)) throw new Error("Names are only allowed in letters");
  if (!validatePassword(password, admin_id, email)) {
    throw new Error("The password needs to be 8-64 characters long, including at least one uppercase and lowercase letter, one numeric character, and one special character, and does not include the student ID/email prefix");
  }

  const formData = new FormData();
  formData.append("admin_id", admin_id);
  formData.append("email", email);
  formData.append("fullName", fullName);
  formData.append("password", password);
  if (avatarFile) formData.append("avatar", avatarFile);

  const result = await this.request<ApiResponse<any>>("/admin/register", {
    method: "POST",
    body: formData, // multipart/form-data
  });

  if (!result.success) throw new Error(result.message || "fail to register");
  return result;
}

async login(studentId: string, password: string): Promise<{ token: string; user: any }> {
const result = await this.request<{ token: string; user: any }>('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ student_id:studentId, password }),
});
if (result.success && result.data?.token) {
  this.token = result.data.token;
  localStorage.setItem('auth_token', this.token);
  localStorage.setItem('login_time', Date.now().toString());
  if (result.data.user) {
    const user = result.data.user;
    if (user.avatarUrl && !user.avatarUrl.startsWith('http')) {
      user.avatarUrl = `${API_BASE}${user.avatarUrl}`;
    }
    const uid: string = user.studentId ?? user.id ?? user.student_id ?? String(studentId);
    localStorage.setItem('current_user_id', uid);
    localStorage.setItem(`u:${uid}:user`, JSON.stringify(user));
    const rawBonus = (user as any).bonus ?? 0;
      let bonusNumber: number;

      if (typeof rawBonus === 'string') {
        bonusNumber = parseFloat(rawBonus);
      } else {
        bonusNumber = Number(rawBonus);
      }

      if (!Number.isFinite(bonusNumber)) {
        bonusNumber = 0;
      }

      localStorage.setItem(`u:${uid}:bonus`, bonusNumber.toString());
  }
  
  return result.data;
}
throw new Error(result.message || 'wrong password/id');
}

async resetStudentBonus() {
    return this.request<null>('/student/bonus/reset', {
      method: 'POST',
    });
  }


async login_adm(adminId: string, password: string): Promise<{ token: string; user: any }> {
  const result = await this.request<{ token: string; user: any }>('/admin/login', {
    method: 'POST',
    body: JSON.stringify({ admin_id: adminId, password }),
  });

  if (result.success && result.data?.token) {
    this.token = result.data.token;
    localStorage.setItem('auth_token', this.token);
    localStorage.setItem('login_time', Date.now().toString());
    const user = result.data.user;
    if (user.avatarUrl && !user.avatarUrl.startsWith('http')) {
      user.avatarUrl = `${API_BASE}${user.avatarUrl}`;
    }
    const uid = user.adminId ?? user.id ?? String(adminId);
    localStorage.setItem('current_user_id', uid);
    localStorage.setItem(`u:${uid}:user`, JSON.stringify(user));
    return result.data;
  }
  throw new Error(result.message || 'Invalid admin ID or password');
}
async logout(): Promise<void> {
  // Backend session logout
  try { await this.request('/auth/logout', { method: 'POST' }); } catch { /* ignore */ }
  // clear
  this.token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('login_time');
  //Record and clean up the current user ID (important)
  localStorage.removeItem('current_user_id');
}

async logout_adm(): Promise<void> {
  try { await this.request('/admin/logout', { method: 'POST' }); } catch { /* ignore */ }

  this.token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('login_time');
  localStorage.removeItem('current_user_id');
}


async getAvailableCourses(): Promise<ApiCourse[]> {
  const res = await this.request<ApiCourse[]>('/courses/available');
  return res.data ?? [];
}

      
async adminGetMyCourses(): Promise<ApiCourse[]> {
    const adminId = localStorage.getItem('current_user_id');
    if (!adminId) {
      console.warn('[adminGetMyCourses] no admin_id found');
      return [];
    }

    const res = await this.request<ApiCourse[]>(
      `/courses_admin?admin_id=${encodeURIComponent(adminId)}`
    );
    return res.data ?? [];

  }

async adminDeleteCourse(code: string) {
  const adminId = localStorage.getItem('current_user_id') || '';
  const form = new FormData();
  form.append('admin_id', adminId);
  form.append('code', code);

  return this.request<void>('/delete_course', {
    method: 'POST',
    body: form,
  });
}

async adminGetCourseTasks(courseId: string): Promise<ApiTask[]> {
  const res = await this.request<ApiTask[]>(`/courses_admin/${courseId}/tasks`);
  return res.data ?? [];
}

async adminGetCourseStudentsProgress(courseId: string, taskId?: string): Promise<Array<{ student_id: string; name?: string; progress: number; overdue_count: number;bonus: number;}>> {
  const q = taskId ? `?task_id=${encodeURIComponent(taskId)}` : '';
  const res = await this.request<Array<{ student_id: string; name?: string; progress: number; overdue_count: number;bonus: number;  }>>(`/courses_admin/${encodeURIComponent(courseId)}/students/progress${q}`);
  return res.data ?? [];
}

async adminCreateTask(
  courseId: string,
  payload: Omit<ApiTask, 'id'> & { url?: string | null; percent_contribution?: number }
) {
  return this.request<{ id: number }>(
    `/courses_admin/${encodeURIComponent(courseId)}/tasks/create`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }
  );
}
async adminDeleteTask(
  courseId: string,
  taskId: string | number,
  opts?: { delete_file?: boolean; method?: 'POST' | 'DELETE' }
) {
  const q = opts?.delete_file ? '?delete_file=1' : '';
  const method = opts?.method || 'POST'; 
  return this.request<{}>(
    `/courses_admin/${encodeURIComponent(courseId)}/tasks/${encodeURIComponent(String(taskId))}/delete${q}`,
    { method }
  );
}

async adminEditTask(
  courseId: string,
  taskId: string | number,
  payload: any,
  opts?: { delete_old_file?: boolean; method?: 'PUT' | 'POST' }
) {
  const q = opts?.delete_old_file ? '?delete_old_file=1' : '';
  const method = opts?.method || 'PUT';
  return this.request<{}>(
    `/courses_admin/${encodeURIComponent(courseId)}/tasks/${encodeURIComponent(String(taskId))}${q}`,
    {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }
  );
}
async adminGetCourseMaterials(courseId: string): Promise<ApiMaterial[]> {
  const res = await this.request<ApiMaterial[]>(`/courses_admin/${courseId}/materials`);
  return res.data ?? [];
}

async uploadMaterialFile(file: File, courseId: string) {
  const form = new FormData();
  form.append('file', file);
  form.append('course', courseId); 
  // token
  let token = this.token || '';
  try { token = token || localStorage.getItem('auth_token') || ''; } catch {}
  // send request
  const res = await fetch(`${API_BASE}/courses_admin/upload/material-file`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: form,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`fail!: HTTP ${res.status} ${text}`);
  }

  const json = await res.json();
  // expect: { success: true, data: { url: "..." } }
  if (!json?.success || !json?.data?.url) {
    throw new Error(json?.message || 'fail!');
  }

  // return Effective URL
  return json.data.url as string;
}
async adminCreateMaterial(
  courseId: string,
  payload: { title: string; description?: string; url: string }
) {
  return this.request<{ id: number }>(
    `/courses_admin/${encodeURIComponent(courseId)}/materials/create`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }
  );
}
async adminDeleteMaterial(courseId: string, materialId: string | number) {
  return this.request<{}>(
    `/courses_admin/${encodeURIComponent(courseId)}/materials/${encodeURIComponent(String(materialId))}/delete`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    }
  );
}
async adminUpdateMaterial(
  courseId: string,
  materialId: string | number,
  payload: { title: string; description?: string; url?: string }
) {
  return this.request<{}>(
    `/courses_admin/${encodeURIComponent(courseId)}/materials/${encodeURIComponent(String(materialId))}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }
  );
}
async adminGetCourseQuestions(courseId: string): Promise<ApiQuestion[]> {
  const res = await this.request<ApiQuestion[]>(`/courses_admin/${courseId}/questions`);
  console.log(res)
  return res.data ?? [];
}
async adminCreateCourseQuestion(courseId: string, payload: Omit<ApiQuestion,'id'>) {
  // Map to server-side fields
  const serverBody =
    payload.qtype === 'mcq'
      ? {
          course_code: courseId,
          qtype: payload.qtype,
          title: payload.title,
          description: payload.description,
          text: payload.text,
          keywords: payload.keywords,
          choices: (payload.choices || []).map(c => ({
            label: c.label ?? null,
            order: c.order,
            content: c.content,
            is_correct: c.isCorrect,     
          })),
        }
      : {
          course_code: courseId,
          qtype: payload.qtype,
          title: payload.title,
          description: payload.description,
          text: payload.text,
          keywords: payload.keywords,
          short_answer: payload.answer ?? '',
        };

  const res = await this.request<{ id: number }>(`/courses_admin/${courseId}/questions/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(serverBody),
  });
  console.log(res)
  return res.data; // { id }
}
async adminUpdateCourseQuestion(courseId: string, questionId: string, payload: Omit<ApiQuestion,'id'>) {
  return this.request<any>(`/courses_admin/${courseId}/questions/${questionId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
async adminDeleteCourseQuestion(courseId: string, questionId: string) {
  return this.request<any>(`/courses_admin/${courseId}/questions/${questionId}/delete`, {
    method: 'DELETE',
  });
}
async adminCheckCourseExists(code: string) {
  return this.request<{ exists: boolean }>(`/course_exists?code=${encodeURIComponent(code)}`, {
    method: 'GET',
  });
}
async adminCreateCourse(payload: {
  code: string;
  title: string;
  description?: string;
  illustration?: 'orange' | 'student' | 'admin';
}) {
  const adminId = localStorage.getItem('current_user_id') || '';
  const form = new FormData();

  form.append('admin_id', adminId);
  form.append('code', payload.code);
  form.append('title', payload.title);
  form.append('description', payload.description || '');
  form.append('illustration', payload.illustration || 'admin');

  return this.request<void>('/create_course', {
    method: 'POST',
    body: form,
  });
}
async saveWeeklyPlansToServer(weeklyPlans:WeeklyPlan,
  aiDetails?: any,
  generationReason?: string,
  generationTime?: string
) {
  try {
    const token = localStorage.getItem('auth_token');
    const studentId = localStorage.getItem('current_user_id');
    if (!token || !studentId) {
      console.warn('[saveWeeklyPlansToServer] Missing token or student_id');
      return { ok: false, error: 'unauthorized' };
    }

    const body = {
      student_id: studentId,
      weeklyPlans,
      tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
      source: 'ai',
      meta: {
        aiDetails,
        generationReason,
        generationTime,
      },
    };

    const res = await fetch('/api/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) {
      console.error('[saveWeeklyPlansToServer] Server returned error:', data);
      return { ok: false, error: data };
    }

    console.log('[saveWeeklyPlansToServer] Success:', data);
    return data;

  } catch (err) {
    console.error('[saveWeeklyPlansToServer] Failed:', err);
    return { ok: false, error: err };
}
}
async adminGetStudentRisk(
  courseId: string,
  taskId: string,  
): Promise<Array<{
  student_id: string;
  student_name: string;
  overdue_parts: number;
  consecutive_not_on_time_days: number;
}>> {
  const body: any = { course_id: courseId, task_id: taskId };

  const resp = await this.request<any>('/admin/student_risk_summary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const rows = Array.isArray(resp) ? resp : (resp?.data ?? []);
  return (Array.isArray(rows) ? rows : []).map((r: any) => ({
    student_id: String(r?.student_id ?? ''),
    student_name: String(r?.student_name ?? ''),
    overdue_parts: Number(r?.overdue_parts ?? 0) || 0,
    consecutive_not_on_time_days: Number(r?.consecutive_not_on_time_days ?? 0) || 0,
  }));
}


  async getUserCourses(): Promise<ApiCourse[]> {
    const res = await this.request<ApiCourse[]>('/courses/my');
    return res.data ?? [];
  }
  
  async addCourse(courseId: string): Promise<void> {
    await this.request<ApiResponse<void>>('/courses/add', {
      method: 'POST',
      body: JSON.stringify({ courseId }),
    });
  }

  async removeCourse(courseId: string): Promise<void> {
    await this.request<ApiResponse<void>>(`/courses/${courseId}`, {
      method: 'DELETE',
    });
  }

  
  
  async updateTaskProgress(taskId: string, progress: number): Promise<void> {
    await this.request<ApiResponse<void>>(`/tasks/${taskId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ progress }),
    });
  }

  // get  the progress of all tasks for students
  async getStudentTaskProgress(): Promise<Array<{
    task_id: number;
    progress: number;
    updated_at?: string;
  }>> {
    const res = await this.request<Array<{
      task_id: number;
      progress: number;
      updated_at?: string;
    }>>('/student/progress');
    return res.data ?? [];
  }

  //get the progress of all tasks under a specific course
  async getCourseTasksProgress(courseCode: string): Promise<Array<{
    task_id: number;
    task_title: string;
    progress: number;
    deadline?: string;
  }>> {
    const res = await this.request<Array<{
      task_id: number;
      task_title: string;
      progress: number;
      deadline?: string;
    }>>(`/courses/${courseCode}/tasks/progress`);
    return res.data ?? [];
  }

  // Get individual task progress details
  async getTaskProgressDetail(taskId: string): Promise<{
    task_id: number;
    progress: number;
    student_id: string;
  }> {
    const res = await this.request<{
      task_id: number;
      progress: number;
      student_id: string;
    }>(`/tasks/${taskId}/progress`);
    return res.data ?? { task_id: parseInt(taskId), progress: 0, student_id: '' };
  }

async addBonus(delta: number = 0.1): Promise<number> {
  const result = await this.request<{ bonus: string | number }>('/student/bonus/add', {
    method: 'POST',
    body: JSON.stringify({ delta }),
  });

  if (result.success && result.data) {
    const rawBonus = result.data.bonus;

    let bonusNumber: number;
    if (typeof rawBonus === 'string') {
      bonusNumber = parseFloat(rawBonus);
    } else {
      bonusNumber = Number(rawBonus);
    }

    if (!Number.isFinite(bonusNumber)) {
      throw new Error('Invalid bonus from server');
    }

    return bonusNumber;
  }

  throw new Error(result.message || 'Failed to update bonus');
}


  async getPreferences(): Promise<ApiPreferences> {
    const res = await this.request<ApiPreferences>('/preferences');
    return res.data ?? {
      dailyHours: 2,
      weeklyStudyDays: 5,
      avoidDays: [],
      saveAsDefault: false,
      description: '',
    };
  }

  async savePreferences(preferences: ApiPreferences): Promise<void> {
    await this.request<ApiResponse<void>>('/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }


  async getWeeklyPlan(weekOffset: number): Promise<ApiPlanItem[]> {
    const res = await this.request<ApiPlanItem[]>(`/plans/weekly/${weekOffset}`);
    return res.data ?? [];
  }


  async getAllWeeklyPlans(): Promise<Record<string, ApiPlanItem[]>> {
  const res = await this.request<Record<string, ApiPlanItem[]>>('/weekly/all');
  return res.data ?? {};   
}
  async saveWeeklyPlan(weekOffset: number, plan: ApiPlanItem[]): Promise<void> {
    await this.request<ApiResponse<void>>(`/plans/weekly/${weekOffset}`, {
      method: 'PUT',
      body: JSON.stringify({ plan }),
    });
  }




  
  async downloadMaterial(materialId: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/materials/${materialId}/download`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    return await response.blob();
  }
  
  async generateAIPlan(): Promise<any> {
  try {
    const res = await this.request<any>('/generate', { method: 'POST' });

    console.log("✅ Original response of AI plan:", res);
    
    if (!res) {
      console.error("❌ The backend returns an empty response");
      return null;
    }
    
    if (!res.success) {
      console.error("❌ Backend return failed:", res.message);
      return null;
    }
    
    // Extract actual AI plan data and save the metadata of the entire response
    const aiPlan = res.data;
    aiPlan.saved = res.saved !== undefined ? res.saved : aiPlan.saved;
    aiPlan.plan_id = res.plan_id !== undefined ? res.plan_id : aiPlan.plan_id;
    
    console.log("🧩 Extracted AI plan data:", aiPlan);
    
    if (!aiPlan) {
      console.error("❌ AI plan data is empty");
      return null;
    }
    
    return aiPlan;

  } catch (err) {
    console.error("❌ Failed to obtain AI learning plan", err);
    return null;
  }
}

async getCourseTasks(courseCode: string): Promise<ApiTask[]> {
  const res = await this.request<unknown[]>(
    `/courses/${encodeURIComponent(courseCode)}/tasks`,
    { method: 'GET', headers: { 'Content-Type': 'application/json' } }
  );

  if (!res?.success) {
    throw new Error(res?.message || 'Failed to fetch course tasks');
  }

  const list = Array.isArray(res.data) ? res.data : [];
  return list.map((t: any): ApiTask => ({
    id: String(t.id),
    title: t.title,
    deadline: t.deadline,
    brief: t.brief,
    percentContribution: t.percentContribution ?? t.percent_contribution ?? 0,
    url: t.url ?? null, 
  }));
}
  // Obtain a list of learning materials

  async getCourseMaterials(courseId: string): Promise<Array<{
    id: string;
    title: string;
    fileType: string;
    fileSize: string;
    description: string;
    uploadDate: string;
  }>> {
      const res = await this.request<Array<{
      id: string;
      title: string;
      fileType: string;
      fileSize: string;
      description: string;
      uploadDate: string;
    }>>(`/courses/${courseId}/materials`);
    return res.data ?? [];
  }

  // Check the authentication status
  isAuthenticated(): boolean {
    return !!this.token || !!localStorage.getItem('auth_token');
  }

  // Initialization (restoring token from localStorage)
  initialize(): void {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      this.token = storedToken;
    }
  }

  async getMessages(): Promise<Message[]> {
    const studentId = localStorage.getItem('current_user_id');
    if (!studentId) {
      console.warn('No student_id found, returning empty message list');
      return [];
    }

    const res = await this.request<Message[]>(`/reminders/${studentId}/`, { method: 'GET' });
    if (!res.success) {
      console.error('Failed to fetch reminders:', res.message);
      return [];
    }
    return res.data ?? [];
  }


  async markMessageAsRead(messageId: string): Promise<void> {
    await this.request(`/reminders/${messageId}/mark-as-read`, { method: 'POST' });
  }

  async markMessagesAsRead(messageIds: string[]): Promise<void> {
    await this.request(`/reminders/mark-as-read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: messageIds }),
    });
  }

}

export const apiService = new ApiService();
apiService.initialize();

export default apiService;