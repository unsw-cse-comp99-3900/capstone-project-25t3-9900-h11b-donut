// API服务层 - 后端集成接口
const API_BASE = 'http://localhost:3001/api';

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

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // 用户认证
  async login(email: string, password: string): Promise<{ token: string; user: any }> {
    const result = await this.request<ApiResponse<{ token: string; user: any }>>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (result.success && result.data.token) {
      this.token = result.data.token;
      localStorage.setItem('auth_token', this.token);
    }
    
    return result.data;
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' });
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  // 课程管理
  async getAvailableCourses(): Promise<ApiCourse[]> {
    const result = await this.request<ApiResponse<ApiCourse[]>>('/courses/available');
    return result.data || [];
  }

  async getUserCourses(): Promise<ApiCourse[]> {
    const result = await this.request<ApiResponse<ApiCourse[]>>('/courses/my');
    return result.data || [];
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
    const result = await this.request<ApiResponse<ApiTask[]>>(`/courses/${courseId}/tasks`);
    return result.data || [];
  }

  async updateTaskProgress(taskId: string, progress: number): Promise<void> {
    await this.request<ApiResponse<void>>(`/tasks/${taskId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ progress }),
    });
  }

  // 用户偏好
  async getPreferences(): Promise<ApiPreferences> {
    const result = await this.request<ApiResponse<ApiPreferences>>('/preferences');
    return result.data || {
      dailyHours: 2,
      weeklyStudyDays: 5,
      avoidDays: [],
      saveAsDefault: false,
      description: ''
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
    const result = await this.request<ApiResponse<ApiPlanItem[]>>(`/plans/weekly/${weekOffset}`);
    return result.data || [];
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
    const result = await this.request<ApiResponse<Array<{
      id: string;
      title: string;
      fileType: string;
      fileSize: string;
      description: string;
      uploadDate: string;
    }>>>(`/courses/${courseId}/materials`);
    
    return result.data || [];
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