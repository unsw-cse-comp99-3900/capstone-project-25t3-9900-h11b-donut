// API服务层 - 后端集成接口
import { coursesStore } from '../store/coursesStore';
import { preferencesStore } from '../store/preferencesStore'; 
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

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${endpoint}`;

  // 先把调用方传入的 headers 标准化
  const headers = new Headers(options.headers as HeadersInit | undefined);
 
  //  兜底同步 token：优先 this.token，没有则从 localStorage 取
  let token = this.token;
  if (!token) {
    try { token = localStorage.getItem('auth_token') || ''; } catch { token = ''; }
    // 可选：把兜底到的 token 回写到实例，后续就不用每次 localStorage 了
    if (token) this.token = token;
  }

  // 统一补充鉴权头（如果有且没被显式覆盖）
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // 根据 body 类型**有条件地**设置 Content-Type（你原逻辑保留）
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
    // 其它情况（比如直接传对象）不建议；如果要支持，可在这里 JSON 化
  }

  const config: RequestInit = {
    ...options,
    headers,                 // 用整理过的 headers
  };

  try {
    const response = await fetch(url, config);

    //  先尝试拿文本→JSON（避免二次读取 body）
    const text = await response.text();
    let payload: ApiResponse<T> | null = null;
    try { payload = text ? JSON.parse(text) : null; } catch { payload = null; }

    //  统一拦截 401（未登录/过期/被挤下线）
    if (response.status === 401) {
      const code = (payload as any)?.code || 'UNAUTHORIZED';

      // 清空本地会话态
      try {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        localStorage.removeItem('current_user_id');
      } catch {}

      // 若是被挤下线给出提示
      if (code === 'KICKED') {
        try { alert('你的账号在另一处登录，你已下线'); } catch {}
      }

      // 回到登录页
      try { window.location.href = '#/login'; } catch {}

      // 返回统一失败对象，防止上层崩
      return { success: false, message: 'Unauthorized', data: null as unknown as T };
    }

    // [改5] 如果后端本来就返回 ApiResponse 结构，直接返回
    if (payload && typeof (payload as any).success === 'boolean') {
      return payload as ApiResponse<T>;
    }

    // [改6] 兜底：按 HTTP 状态构造一个 ApiResponse
    return {
      success: response.ok,
      message: response.ok ? 'OK' : `HTTP ${response.status}`,
      data: null as unknown as T,
    };
  } catch (error) {
    console.error('API request failed:', error);
    throw error; // 网络级错误保留抛出
  }
}

  async searchCourses(q: string): Promise<ApiCourse[]> {
    const res = await this.request<ApiCourse[]>('/courses/search?q=' + encodeURIComponent(q));
    // 后端返回的是 {code,title,description,illustration}
    const raw = (res.data ?? []) as any[];
    return raw.map(r => ({
      id: r.code,
      title: r.title,
      description: r.description,
      illustration: r.illustration as 'orange'|'student'|'admin',
    }));
  }
  // 用户认证
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
    formData.append("avatar", avatarFile); // 后端用 request.FILES.get("avatar")
  }

  const result = await this.request<ApiResponse<any>>("/auth/register", {
    method: "POST",
    body: formData, //  不再用 JSON.stringify
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
  }
  await coursesStore.refreshAvailableCourses();
  await coursesStore.refreshMyCourses();
  await preferencesStore.loadPreferencesFromAPI();
  return result.data;
}
throw new Error(result.message || 'wrong password/id');
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
    window.location.hash = '/admin/home';
    return result.data;
  }


  throw new Error(result.message || 'Invalid admin ID or password');
}
async logout(): Promise<void> {
  // 后端会话登出
  try { await this.request('/auth/logout', { method: 'POST' }); } catch { /* ignore */ }
  // 清空鉴权态
  this.token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('login_time');
  //记录并清理当前用户 ID（关键）
  const uid = localStorage.getItem('current_user_id');
  localStorage.removeItem('current_user_id');
  // 清空前端“内存”状态（避免下个账号看到旧内存）
  try { coursesStore.reset(); } catch {}
}

async logout_adm(): Promise<void> {
  try { await this.request('/admin/logout', { method: 'POST' }); } catch { /* ignore */ }
  // 清空鉴权态
  this.token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('login_time');
  const uid = localStorage.getItem('current_user_id');
  localStorage.removeItem('current_user_id');
}

  // 课程管理
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
//这个删除函数要改，不完善
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
  // 发请求
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
  // 预期返回 { success: true, data: { url: "..." } }
  if (!json?.success || !json?.data?.url) {
    throw new Error(json?.message || 'fail!');
  }

  // 返回文件可访问路径
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
  // 映射到服务端字段
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

  // 用户偏好
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

  // 学习计划
  async getWeeklyPlan(weekOffset: number): Promise<ApiPlanItem[]> {

    const res = await this.request<ApiPlanItem[]>(`/plans/weekly/${weekOffset}`);
    return res.data ?? [];
  }

  async saveWeeklyPlan(weekOffset: number, plan: ApiPlanItem[]): Promise<void> {
    await this.request<ApiResponse<void>>(`/plans/weekly/${weekOffset}`, {
      method: 'PUT',
      body: JSON.stringify({ plan }),
    });
  }

  // 学习材料下载
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
    console.log("✅ AI 计划已从后端获取:", res);

    // 🔧 关键修复：兼容后端直接返回JSON而非 {data: ...}
    const aiPlan = (res && res.data) ? res.data : res;

    console.log("🧩 实际可用的 AI 计划:", aiPlan);
    return aiPlan ?? null;

  } catch (err) {
    console.error("❌ 获取 AI 学习计划失败:", err);
    return null;
  }
}

async getCourseTasks(courseCode: string): Promise<ApiTask[]> {
  // 你的 request<T> 返回的是 ApiResponse<T>（{ success, data, message? }）
  const res = await this.request<unknown[]>(
    `/courses/${encodeURIComponent(courseCode)}/tasks`,
    { method: 'GET', headers: { 'Content-Type': 'application/json' } }
  );

  if (!res?.success) {
    throw new Error(res?.message || 'Failed to fetch course tasks');
  }

  const list = Array.isArray(res.data) ? res.data : [];

  // 在 api 层做一次 snake_case -> camelCase 的映射，外部只用 ApiTask
  return list.map((t: any): ApiTask => ({
    id: String(t.id),
    title: t.title,
    deadline: t.deadline,
    brief: t.brief,
    percentContribution: t.percentContribution ?? t.percent_contribution ?? 0,
    url: t.url ?? null, 
  }));
}
  // 获取学习材料列表
  async getCourseMaterials(courseId: string): Promise<Array<{
    id: string;
    title: string;
    fileType: string;
    fileSize: string;
    description: string;
    uploadDate: string;
  }>> {
    // const result = await this.request<ApiResponse<Array<{
    //   id: string;
    //   title: string;
    //   fileType: string;
    //   fileSize: string;
    //   description: string;
    //   uploadDate: string;
    // }>>>(`/courses/${courseId}/materials`);
    
    // return result.data || [];
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

  // 检查认证状态
  isAuthenticated(): boolean {
    return !!this.token || !!localStorage.getItem('auth_token');
  }

  // 初始化（从localStorage恢复token）
  initialize(): void {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      this.token = storedToken;
    }
  }

  // 消息功能 - 模拟数据
  async getMessages(): Promise<Message[]> {
    const now = new Date();
    const mockMessages: Message[] = [
      // Due Alerts - 与现有作业相关
      {
        id: '1',
        type: 'due_alert',
        title: 'Assignment Due Soon',
        preview: 'Assignment "Final Project Report" for COMP1234 is due in 2 days',
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(), // 2小时前
        isRead: false,
        courseId: 'COMP1234',
        dueTime: new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000).toISOString() // 2天后
      },
      {
        id: '2',
        type: 'due_alert',
        title: 'Quiz Reminder',
        preview: 'Quiz "Week 5 Assessment" for MATH5678 is due tomorrow',
        timestamp: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(), // 6小时前
        isRead: true,
        courseId: 'MATH5678',
        dueTime: new Date(now.getTime() + 1 * 24 * 60 * 60 * 1000).toISOString() // 1天后
      },
      
      // Admin DDL Updates - 管理员修改DDL提醒
      {
        id: '9',
        type: 'due_alert',
        title: 'Deadline Updated',
        preview: 'Admin has extended the deadline for "Midterm Exam" in COMP1234 to next Friday',
        timestamp: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), // 30分钟前
        isRead: false,
        courseId: 'COMP1234',
        dueTime: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString() // 7天后
      },
      {
        id: '10',
        type: 'due_alert',
        title: 'Deadline Changed',
        preview: 'Admin has moved up the deadline for "Lab Report" in PHYS101 to this Wednesday',
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(), // 2小时前
        isRead: false,
        courseId: 'PHYS101',
        dueTime: new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000).toISOString() // 2天后
      },
      
      // Nightly Notices - 模拟数据
      {
        id: '3',
        type: 'nightly_notice',
        title: 'Yesterday\'s Plan Incomplete',
        preview: 'You didn\'t complete all tasks from yesterday\'s study plan. The system has automatically rescheduled your plan at 00:00.',
        timestamp: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(), // 12小时前
        isRead: false
      },
      {
        id: '4',
        type: 'nightly_notice',
        title: 'Auto-reschedule Completed',
        preview: 'Your unfinished tasks from yesterday have been automatically rescheduled to today\'s plan at 00:00.',
        timestamp: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString(), // 1天前
        isRead: true
      },
      
      // Weekly Bonuses - 模拟数据
      {
        id: '5',
        type: 'weekly_bonus',
        title: 'Weekly Achievement',
        preview: 'Great job! You completed all tasks on time this week',
        timestamp: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3天前
        isRead: false
      },
      {
        id: '6',
        type: 'weekly_bonus',
        title: 'Bonus Points Awarded',
        preview: 'You earned 0.01 bonus points for perfect weekly completion',
        timestamp: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7天前
        isRead: true
      },
      
      // System Notifications - 模拟数据
      {
        id: '7',
        type: 'system_notification',
        title: 'System Update',
        preview: 'New features have been added to your study planner',
        timestamp: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString(), // 1小时前
        isRead: false
      },
      {
        id: '8',
        type: 'system_notification',
        title: 'Welcome Message',
        preview: 'Welcome to Study Planner! Start by setting up your preferences',
        timestamp: new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000).toISOString(), // 10天前
        isRead: true
      }
    ];

    return mockMessages;
  }

  async markMessageAsRead(messageId: string): Promise<void> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 200));
    console.log(`Message ${messageId} marked as read`);
  }

  async markMessagesAsRead(messageIds: string[]): Promise<void> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 300));
    console.log(`Messages ${messageIds.join(', ')} marked as read`);
  }
}

export const apiService = new ApiService();
apiService.initialize();

export default apiService;