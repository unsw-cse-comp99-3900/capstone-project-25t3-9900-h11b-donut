// API服务层 - 后端集成接口
import { coursesStore } from '../store/coursesStore';
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
    // 如果走 Cookie/Session，需要携带 cookie：
    // credentials: 'include',
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

      // 若是被挤下线给出提示（按你项目改成全局 toast 也可以）
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
  async register(student_id: string, name: string,email: string, password: string, avatarFile?: File) {
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

    return result.data;
  }
  // 把后端返回的 message 暴露给 UI
  throw new Error(result.message || 'wrong password/id');
}

  async logout(): Promise<void> {
  // 1) 后端会话登出（即使失败也做本地清理）
  try { await this.request('/auth/logout', { method: 'POST' }); } catch { /* ignore */ }

  // 2) 清空鉴权态
  this.token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('login_time');

  // 3) 记录并清理当前用户 ID（关键）
  const uid = localStorage.getItem('current_user_id');
  localStorage.removeItem('current_user_id');
  // 5) 清空前端“内存”状态（避免下个账号看到旧内存）
  try { coursesStore.reset(); } catch {}

}
  // 课程管理
  async getAvailableCourses(): Promise<ApiCourse[]> {
    const res = await this.request<ApiCourse[]>('/courses/available');
    return res.data ?? [];
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

  // 任务管理
  async getCourseTasks(courseId: string): Promise<ApiTask[]> {

    const res = await this.request<ApiTask[]>(`/courses/${courseId}/tasks`);
    return res.data ?? [];
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
    // const result = await this.request<ApiResponse<ApiPlanItem[]>>(`/plans/weekly/${weekOffset}`);
    // return result.data || [];
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
}

export const apiService = new ApiService();
apiService.initialize();

export default apiService;