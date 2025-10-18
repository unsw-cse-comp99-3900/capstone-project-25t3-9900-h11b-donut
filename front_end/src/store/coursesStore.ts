import { apiService } from '../services/api';

export type Course = {
  id: string;            // 对应后端 CourseCatalog.code
  title: string;         // CourseCatalog.title
  desc: string;          // CourseCatalog.description
  illustration: 'orange' | 'student' | 'admin';
};

export type Task = {
  id: string;
  title: string;
  deadline: string;
  brief?: string;
  percentContribution?: number;
};

export type Deadline = {
  id: string;
  title: string;
  course: string;
  dueIn: string;
  progress: number;
  color: string;
  dueAt: number;
};

type Listener = () => void;

class CoursesStore {
  // 来自后端的可搜索课程与我的课程
  availableCourses: Course[] = [];
  myCourses: Course[] = [];

  // 缓存：任务与进度
  private tasksByCourse: Record<string, Task[]> = {};
  private deadlines: Deadline[] = [];
  private progressByDeadline: Record<string, number> = {};

  private listeners: Listener[] = [];
  
  constructor() {
    const token = localStorage.getItem('auth_token');
    // 启动时拉取我的课程与可用课程


    const uid = localStorage.getItem('current_user_id');
  if (uid) {
    const raw = localStorage.getItem(`u:${uid}:myCourses:v1`);
    if (raw) {
      this.myCourses = JSON.parse(raw);
      this.notify(); 
    }
  }
    this.loadAvailableCourses();
    if (token) this.loadMyCoursesFromAPI(); 
  }

  subscribe(fn: Listener) {
    this.listeners.push(fn);
    return () => { this.listeners = this.listeners.filter(l => l !== fn); };
  }

  private notify() { this.listeners.forEach(l => l()); }

  getCourseTasks(courseId: string): Task[] {
      return this.tasksByCourse[courseId] ?? [];
    } 

  private async loadAvailableCourses() {
    try {
      const apiCourses = await apiService.getAvailableCourses();
      this.availableCourses = apiCourses.map(c => ({
        id: c.id,
        title: c.title,
        desc: c.description,
        illustration: c.illustration
      }));
      this.notify();
    } catch (e) {
      console.warn('Failed to load available courses:', e);
    }
  }

  private async loadMyCoursesFromAPI() {
    try {
      const apiCourses = await apiService.getUserCourses();
      this.myCourses = apiCourses.map(c => ({
        id: c.id,
        title: c.title,
        desc: c.description,
        illustration: c.illustration
      }));
      await this.syncDeadlinesFromCourses(); // 拉取任务再生成 deadlines
      const uid = (typeof window !== 'undefined') ? localStorage.getItem('current_user_id') : null;
      if (uid) {
        localStorage.setItem(`u:${uid}:myCourses:v1`, JSON.stringify(this.myCourses));
        // 把 deadlines 也缓存起来
        try {
          localStorage.setItem(`u:${uid}:deadlines:v1`, JSON.stringify(this.deadlines));
        } catch { /* 存储满了可忽略 */ }
      }
      this.notify();
    } catch (error) {
      console.warn('Failed to load my courses from API:', error);
    }
  }
  //這裡解決了重新登錄後出現前一個賬戶的課程！！！
  public async refreshMyCourses(): Promise<void> {
  await this.loadMyCoursesFromAPI();
  }
  public async refreshAvailableCourses(force = false) {
  if (force || this.availableCourses.length === 0) {
    await this.loadAvailableCourses();
    this.notify();
  }
}

  public reset(): void {
  this.availableCourses = this.availableCourses; 
  this.myCourses = [];
  this.tasksByCourse = {};
  this.deadlines = [];
  this.progressByDeadline = {};
  this.notify();
  }

  async searchCourses(q: string): Promise<Course[]> {
    const list = await apiService.searchCourses(q);
    return list.map(c => ({
      id: c.id,
      title: c.title,
      desc: c.description,
      illustration: (c.illustration as any) || 'orange'
    }));
  }

  async addCourse(courseId: string) {
    // 若已存在则不重复添加
    const exists = this.myCourses.find(c => c.id.toLowerCase() === courseId.toLowerCase());
    if (exists) return;
    const found = this.availableCourses.find(c => c.id.toLowerCase() === courseId.toLowerCase());
    if (!found) return;

    // 乐观更新：立即加入 UI 并通知渲染
    this.myCourses = [...this.myCourses, found];
    this.notify();

    // 后台并行：添加到后端并刷新“我的课程”再校准 deadlines
    (async () => {
      try {
        await apiService.addCourse(courseId);
        const apiCourses = await apiService.getUserCourses();
        this.myCourses = apiCourses.map(c => ({
          id: c.id,
          title: c.title,
          desc: c.description,
          illustration: c.illustration
        }));
        await this.syncDeadlinesFromCourses();
        this.notify();
      } catch (error) {
        console.warn('Failed to add course via API:', error);
        // 后端失败时保留乐观结果（可按需提示用户）
        await this.syncDeadlinesFromCourses();
        this.notify();
      }
    })();
  }

  async removeCourse(courseId: string) {
    await apiService.removeCourse(courseId);
    // 清理缓存
    delete this.tasksByCourse[courseId];
    this.myCourses = this.myCourses.filter(c => c.id !== courseId);
    await this.syncDeadlinesFromCourses();
    this.notify();
  }

  // 按需加载任务（首次从后端获取并缓存）
  async getCourseTasksAsync(courseId: string): Promise<Task[]> {
    if (!this.tasksByCourse[courseId]) {
      const apiTasks = await apiService.getCourseTasks(courseId);
      this.tasksByCourse[courseId] = apiTasks.map(t => ({
        id: String(t.id),
        title: t.title,
        deadline: t.deadline,
        brief: t.brief,
        percentContribution: (t as any).percent_contribution ?? t.percentContribution
      }));
      await this.syncDeadlinesFromCourses();
      this.notify();
    }
    return this.tasksByCourse[courseId];
  }

  // 同步 deadlines（依赖 tasks 缓存）
  private async syncDeadlinesFromCourses() {
    const list: Deadline[] = [];
    // 为每门课确保任务缓存
    for (const course of this.myCourses) {
      if (!this.tasksByCourse[course.id]) {
        try { await this.getCourseTasksAsync(course.id); } catch { /* ignore */ }
      }
      const tasks = this.tasksByCourse[course.id] || [];
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
    this.deadlines = list;
  }

  getDeadlines(): Deadline[] {
    return this.deadlines.map(d => ({ ...d, dueIn: this.calculateDueInFromTs(d.dueAt) }));
  }

  getColorByCourse(courseId: string): string {
    const courseColors: Record<string, string> = {
      'COMP9900': '#F6B48E', 'COMP9417': '#6CB7FF','COMP6080': '#F8A0B9','COMP9337': '#A3E4C9'
    };
    if (!courseColors[courseId]) {
      let hash = 0; for (let i=0;i<courseId.length;i++) { hash = courseId.charCodeAt(i) + ((hash<<5)-hash); }
      const colors = ['#F6B48E','#6CB7FF','#F8A0B9','#A3E4C9','#D6A2E8','#FFD166','#06D6A0','#118AB2'];
      return colors[Math.abs(hash) % colors.length];
    }
    return courseColors[courseId];
  }

  async setProgress(id: string, progress: number) {
    const [_, taskId] = id.split('-');
    if (taskId) {
      await apiService.updateTaskProgress(taskId, progress);
    }
    this.progressByDeadline[id] = progress;
    const idx = this.deadlines.findIndex(d => d.id === id);
    if (idx !== -1) this.deadlines[idx] = { ...this.deadlines[idx], progress };
    this.notify();
  }

  private calculateDueInFromTs(dueAt: number): string {
    const diffMs = dueAt - Date.now();
    const abs = Math.abs(diffMs);
    const diffDays = Math.floor(abs / (1000*60*60*24));
    const diffHours = Math.floor((abs % (1000*60*60*24)) / (1000*60*60));
    const diffMins = Math.floor((abs % (1000*60*60)) / (1000*60));
    if (diffMs < 0) return `- ${diffDays}d ${diffHours}h ${diffMins}m`;
    return `${diffDays}d ${diffHours}h ${diffMins}m`;
  }

  // 计算课程整体进度（按任务权重加权）
  getCourseProgress(courseId: string): number {
    const tasks = this.tasksByCourse[courseId] || [];
    if (tasks.length === 0) return 0;

    let totalWeight = 0;
    let completedWeight = 0;

    tasks.forEach(task => {
      const taskKey = `${courseId}-${task.id}`;
      const progress = this.progressByDeadline[taskKey] ?? 0;
      const weight = task.percentContribution ?? (100 / tasks.length);
      totalWeight += weight;
      completedWeight += (progress / 100) * weight;
    });

    return totalWeight > 0 ? Math.round((completedWeight / totalWeight) * 100) : 0;
  }

  public getLatestDeadline(): Date | null {
    let latest: Date | null = null;
    for (const course of this.myCourses) {
      const tasks = this.tasksByCourse[course.id] || [];
      for (const t of tasks) {
        if (t.deadline) {
          const d = new Date(t.deadline);
          if (!latest || d > latest) latest = d;
        }
      }
    }
    return latest;
  }
}

export const coursesStore = new CoursesStore();