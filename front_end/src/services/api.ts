// API服务层 - 后端集成接口
//const API_BASE = 'http://localhost:3001/api';
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
  private token: string | null = null;

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

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${endpoint}`;

  // 先把调用方传入的 headers 标准化
  const headers = new Headers(options.headers as HeadersInit | undefined);

  // 补充鉴权头（如果有）
  if (this.token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${this.token}`);
  }

  // 根据 body 类型**有条件地**设置 Content-Type
  const body = options.body as any;
  if (body === undefined || body === null) {
    // 没有 body：不要设置 Content-Type
    headers.delete('Content-Type');
  } else if (body instanceof FormData || body instanceof Blob || body instanceof File) {
    // 二进制/表单：不要设置 Content-Type（浏览器会自动加 multipart/form-data 或相应类型）
    headers.delete('Content-Type');
  } else if (typeof body === 'string') {
    // 字符串（通常是 JSON.stringify 后的文本）
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
  } else {
    // 其它情况（比如直接传对象）不建议；如果要支持，可在这里 JSON 化
    // 为保持当前调用方式，这里不做处理。
  }

  const config: RequestInit = {
    ...options,
    headers,                 // 用整理过的 headers
    // 如果走 Cookie/Session，需要携带 cookie：
    // credentials: 'include',
  };

  try {
    const response = await fetch(url, config);
    // 兜底解析：先拿文本再尝试 JSON
    const text = await response.text();
    let payload: ApiResponse<T> | null = null;
    try { payload = text ? JSON.parse(text) : null; } catch { payload = null; }

    if (payload && typeof payload.success === 'boolean') {
      return payload; 
    }

    return {
      success: response.ok,
      message: response.ok ? 'OK' :  `HTTP ${response.status}`,
      data: null as unknown as T,
    };
  } catch (error) {
    console.error('API request failed:', error);
    throw error; // 网络级错误保留抛出
  }
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
      localStorage.setItem('user', JSON.stringify(user));
    }
    return result.data;
  }
  // 把后端返回的 message 暴露给 UI
  throw new Error(result.message || 'wrong password/id');
}

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' });
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }

  // 课程管理
  async getAvailableCourses(): Promise<ApiCourse[]> {
    // const result = await this.request<ApiResponse<ApiCourse[]>>('/courses/available');
    // return result.data || [];
    const res = await this.request<ApiCourse[]>('/courses/available');
    return res.data ?? [];
  }

  async getUserCourses(): Promise<ApiCourse[]> {
    // const result = await this.request<ApiResponse<ApiCourse[]>>('/courses/my');
    // return result.data || [];
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
    // const result = await this.request<ApiResponse<ApiTask[]>>(`/courses/${courseId}/tasks`);
    // return result.data || [];
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
    // const result = await this.request<ApiResponse<ApiPreferences>>('/preferences');
    // return result.data || {
    //   dailyHours: 2,
    //   weeklyStudyDays: 5,
    //   avoidDays: [],
    //   saveAsDefault: false,
    //   description: ''
    // };
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