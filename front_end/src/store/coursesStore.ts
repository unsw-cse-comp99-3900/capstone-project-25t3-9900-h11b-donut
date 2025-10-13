import { apiService } from '../services/api';

export type Course = {
  id: string;
  title: string;
  desc: string;
  illustration: 'orange' | 'student' | 'admin';
};

export type Task = {
  id: string;
  title: string;
  deadline: string;
  brief?: string;
  percentContribution?: number; // 任务部分占总进度的百分比
};

export type Deadline = {
  id: string;
  title: string;
  course: string;
  dueIn: string;
  progress: number;
  color: string;
  dueAt: number; // 原始截止时间戳（毫秒）
};

type Listener = () => void;

class CoursesStore {
  // 可被搜索到的课程（模拟后端数据）
  availableCourses: Course[] = [
    { id: 'COMP9900', title: 'COMP9900', desc: 'Info Tech Project', illustration: 'admin' },
    { id: 'COMP9417', title: 'COMP9417', desc: 'Machine Learning', illustration: 'student' },
    { id: 'COMP6080', title: 'COMP6080', desc: 'Web Front-End', illustration: 'orange' },
    { id: 'COMP9337', title: 'COMP9337', desc: 'Cyber Security', illustration: 'admin' }
  ];

  // 课程任务（统一数据源，供 CourseDetail 使用）
  private tasksByCourse: Record<string, Task[]> = {
    'COMP9900': [
      { id: '1', title: 'Project Proposal', deadline: '2025-12-15', brief: 'Submit initial project proposal', percentContribution: 30 },
      { id: '2', title: 'Mid-term Report', deadline: '2025-11-20', brief: 'Provide project progress report', percentContribution: 40 },
      { id: '3', title: 'Final Presentation', deadline: '2025-11-19', brief: 'Deliver final presentation and report', percentContribution: 30 }
    ],
    'COMP9417': [
      { id: '1', title: 'Assignment 1', deadline: '2025-11-30', brief: 'Implement linear regression', percentContribution: 50 },
      { id: '2', title: 'Assignment 2', deadline: '2025-12-20', brief: 'Build a neural network', percentContribution: 50 }
    ],
    'COMP6080': [],
    'COMP9337': [
      { id: '1', title: 'Security Audit', deadline: '2025-11-25', brief: 'Perform a security audit', percentContribution: 60 },
      { id: '2', title: 'Penetration Test', deadline: '2025-12-05', brief: 'Conduct a penetration test', percentContribution: 40 }
    ]
  };

  // 我的课程（从 API 加载）
  myCourses: Course[] = [];

  // Deadlines 与进度（集中在 coursesStore）
  private deadlines: Deadline[] = [];
  private progressByDeadline: Record<string, number> = {};

  private listeners: Listener[] = [];
  
  constructor() {
    this.loadMyCoursesFromAPI();
  }

  subscribe(fn: Listener) {
    this.listeners.push(fn);
    return () => {
      this.listeners = this.listeners.filter(l => l !== fn);
    };
  }

  private notify() {
    this.listeners.forEach(l => l());
  }

  private async loadMyCoursesFromAPI() {
    try {
      const apiCourses = await apiService.getUserCourses();
      this.myCourses = apiCourses.map(course => ({
        id: course.id,
        title: course.title,
        desc: course.description,
        illustration: course.illustration as 'orange' | 'student' | 'admin'
      }));
      this.syncDeadlinesFromCourses();
      this.notify();
    } catch (error) {
      console.warn('Failed to load my courses from API:', error);
      // 降级到本地存储
      this.loadMyCoursesFromLocalStorage();
    }
  }

  private loadMyCoursesFromLocalStorage(): Course[] {
    try {
      const stored = localStorage.getItem('ai-web-my-courses');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.warn('Failed to load my courses from localStorage:', error);
    }
    return [];
  }



  private saveMyCoursesToLocalStorage() {
    try {
      localStorage.setItem('ai-web-my-courses', JSON.stringify(this.myCourses));
    } catch (error) {
      console.warn('Failed to save my courses to localStorage:', error);
    }
  }

  async addCourse(courseId: string) {
    const exists = this.myCourses.find(c => c.id.toLowerCase() === courseId.toLowerCase());
    if (exists) return;
    const found = this.availableCourses.find(c => c.id.toLowerCase() === courseId.toLowerCase());
    if (!found) return;
    
    try {
      await apiService.addCourse(courseId);
      this.myCourses = [...this.myCourses, found];
      this.saveMyCoursesToLocalStorage();
      this.syncDeadlinesFromCourses();
      this.notify();
    } catch (error) {
      console.warn('Failed to add course via API:', error);
      // 降级到本地操作
      this.myCourses = [...this.myCourses, found];
      this.saveMyCoursesToLocalStorage();
      this.syncDeadlinesFromCourses();
      this.notify();
    }
  }

  async removeCourse(courseId: string) {
    try {
      await apiService.removeCourse(courseId);
      this.myCourses = this.myCourses.filter(c => c.id.toLowerCase() !== courseId.toLowerCase());
      this.saveMyCoursesToLocalStorage();
      this.syncDeadlinesFromCourses();
      this.notify();
    } catch (error) {
      console.warn('Failed to remove course via API:', error);
      // 降级到本地操作
      this.myCourses = this.myCourses.filter(c => c.id.toLowerCase() !== courseId.toLowerCase());
      this.saveMyCoursesToLocalStorage();
      this.syncDeadlinesFromCourses();
      this.notify();
    }
  }

  // 统一对外方法：获取指定课程的任务
  getCourseTasks(courseId: string): Task[] {
    return this.tasksByCourse[courseId] ?? [];
  }

  // 获取所有课程的任务映射（公开方法）
  getTasksByCourseMap(): Record<string, Task[]> {
    return { ...this.tasksByCourse };
  }

  // 课程颜色（对外）
  getColor(courseId: string): string {
    return this.getColorByCourse(courseId);
  }

  // 设置某个 deadline 的进度
  async setProgress(id: string, progress: number) {
    try {
      // 解析任务ID格式：courseId-taskId
      const [courseId, taskId] = id.split('-');
      if (courseId && taskId) {
        await apiService.updateTaskProgress(taskId, progress);
      }
      
      this.progressByDeadline[id] = progress;
      const idx = this.deadlines.findIndex(d => d.id === id);
      if (idx !== -1) {
        this.deadlines[idx] = { ...this.deadlines[idx], progress };
      }
      this.notify();
    } catch (error) {
      console.warn('Failed to update task progress via API:', error);
      // 降级到本地操作
      this.progressByDeadline[id] = progress;
      const idx = this.deadlines.findIndex(d => d.id === id);
      if (idx !== -1) {
        this.deadlines[idx] = { ...this.deadlines[idx], progress };
      }
      this.notify();
    }
  }

  // 计算课程整体进度
  getCourseProgress(courseId: string): number {
    const tasks = this.getCourseTasks(courseId);
    if (tasks.length === 0) return 0;
    
    let totalWeight = 0;
    let completedWeight = 0;
    
    tasks.forEach(task => {
      const taskId = `${courseId}-${task.id}`;
      const progress = this.progressByDeadline[taskId] ?? 0;
      const weight = task.percentContribution ?? 100 / tasks.length; // 默认平均分配
      
      totalWeight += weight;
      completedWeight += (progress / 100) * weight;
    });
    
    return totalWeight > 0 ? Math.round((completedWeight / totalWeight) * 100) : 0;
  }

  // 获取 Deadlines（返回前动态计算 dueIn）
  getDeadlines(): Deadline[] {
    // 确保 deadlines 与当前课程/任务同步
    // 注意：myCourses 变化时会在 add/remove 中调用 sync
    return this.deadlines.map(d => ({
      ...d,
      dueIn: this.calculateDueInFromTs(d.dueAt),
    }));
  }

  // ============== 内部实现 ==============

  // 颜色映射（公共方法）
  getColorByCourse(courseId: string): string {
    const courseColors: Record<string, string> = {
      'COMP9900': '#F6B48E',
      'COMP9417': '#6CB7FF', 
      'COMP6080': '#F8A0B9',
      'COMP9337': '#A3E4C9'
    };
    if (!courseColors[courseId]) {
      let hash = 0;
      for (let i = 0; i < courseId.length; i++) {
        hash = courseId.charCodeAt(i) + ((hash << 5) - hash);
      }
      const colors = ['#F6B48E', '#6CB7FF', '#F8A0B9', '#A3E4C9', '#D6A2E8', '#FFD166', '#06D6A0', '#118AB2'];
      return colors[Math.abs(hash) % colors.length];
    }
    return courseColors[courseId];
  }

  // 生成 deadlines（仅对有任务的课程）
  private syncDeadlinesFromCourses() {
    const my = this.myCourses;
    const list: Deadline[] = [];

    my.forEach(course => {
      const tasks = this.getCourseTasks(course.id);
      if (tasks.length > 0) {
        tasks.forEach(task => {
          const dueAt = new Date(task.deadline).getTime();
          const id = `${course.id}-${task.id}`;
          const progress = this.progressByDeadline[id] ?? 0;
          list.push({
            id,
            title: task.title,
            course: course.id,
            dueIn: this.calculateDueInFromTs(dueAt),
            progress,
            color: this.getColorByCourse(course.id),
            dueAt
          });
        });
      }
    });

    this.deadlines = list;
  }

  private calculateDueInFromTs(dueAt: number): string {
    const diffMs = dueAt - Date.now();
    const abs = Math.abs(diffMs);
    const diffDays = Math.floor(abs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((abs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const diffMins = Math.floor((abs % (1000 * 60 * 60)) / (1000 * 60));
    if (diffMs < 0) {
      return `- ${diffDays}d ${diffHours}h ${diffMins}m`;
    }
    return `${diffDays}d ${diffHours}h ${diffMins}m`;
  }

  // 获取所有课程的最后截止日期
  public getLatestDeadline(): Date | null {
    let latestDeadline: Date | null = null;
    
    this.myCourses.forEach(course => {
      const tasks = this.getCourseTasks(course.id);
      tasks.forEach(task => {
        if (task.deadline) {
          const deadline = new Date(task.deadline);
          if (!latestDeadline || deadline > latestDeadline) {
            latestDeadline = deadline;
          }
        }
      });
    });
    
    return latestDeadline;
  }
}

export const coursesStore = new CoursesStore();