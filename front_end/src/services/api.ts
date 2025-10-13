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

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const url = `${API_BASE}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };
    try {
    const response = await fetch(url, config);

    // 尝试解析 JSON；有些错误响应可能不是 JSON，兜底
    const text = await response.text();
    let payload: ApiResponse<T> | null = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = null;
    }

    // 如果能解析成我们的标准返回结构，就直接返回（无论 200 还是 401）
    if (payload && typeof payload.success === 'boolean') {
    return payload;
    }

    // 否则构造一个通用的失败返回
    return {
      success: response.ok,
      message: response.ok ? 'OK' : `HTTP ${response.status}`,
      data: null as unknown as T,
    };
  } catch (error) {
    console.error('API request failed:', error);
    // 只有网络级错误才抛（例如断网/跨域被拦截）
    throw error;
  }
    // try {
    //   const response = await fetch(url, config);
      
    //   if (!response.ok) {
    //     throw new Error(`HTTP error! status: ${response.status}`);
    //   }
      
    //   return await response.json();
    // } catch (error) {
    //   console.error('API request failed:', error);
    //   throw error;
    // }

  }

  // 用户认证

async register(student_id: string,email: string, password: string) {
  const result = await this.request<ApiResponse<any>>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ student_id,email, password }),
  });
  if (!result.success) {
    throw new Error(result.message || 'fail to register');
  }
  return result;
}


  async login(email: string, password: string): Promise<{ token: string; user: any }> {
  const result = await this.request<{ token: string; user: any }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  if (result.success && result.data?.token) {
    this.token = result.data.token;
    localStorage.setItem('auth_token', this.token);
    return result.data;
  }

  // 把后端返回的 message 暴露给 UI
  throw new Error(result.message || '邮箱或密码不正确');
}

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' });
    this.token = null;
    localStorage.removeItem('auth_token');
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