import { apiService } from '../services/api';

export type Course = {
  id: string;            // CourseCatalog.code
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
  url?: string | null;   
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
  availableCourses: Course[] = [];
  myCourses: Course[] = [];

  private tasksByCourse: Record<string, Task[]> = {};
  private deadlines: Deadline[] = [];
  private progressByDeadline: Record<string, number> = {};

  private listeners: Listener[] = [];
  private _inited = false;
  private _loading = false;
  constructor() {
    // const token = localStorage.getItem('auth_token');
    // get my course and available course
    const uid = localStorage.getItem('current_user_id');
  if (uid) {
    const raw = localStorage.getItem(`u:${uid}:myCourses:v1`);
    if (raw) {
      this.myCourses = JSON.parse(raw);
      this.notify(); 
    }
  }
    // this.loadAvailableCourses();
    // if (token) this.loadMyCoursesFromAPI(); 
  }

async ensureLoaded() {
    if (this._inited || this._loading) {
      return;
    }
    this._loading = true;
    const token = localStorage.getItem('auth_token');

    await this.loadAvailableCourses();
    if (token) {
      await this.loadMyCoursesFromAPI();
    }

    this._inited = true;
    this._loading = false;
    this.notify();
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
      
      await this.syncDeadlinesFromCourses(); // load task then load deadlines
      const uid = (typeof window !== 'undefined') ? localStorage.getItem('current_user_id') : null;
      if (uid) {
        localStorage.setItem(`u:${uid}:myCourses:v1`, JSON.stringify(this.myCourses));
        
        try {
          localStorage.setItem(`u:${uid}:deadlines:v1`, JSON.stringify(this.deadlines));
        } catch {  }
      }
      this.notify();
    } catch (error) {
      console.warn('Failed to load my courses from API:', error);
    }
  }
  //This solves the problem of courses appearing in the previous account after logging in again!!!
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
    // if exist return
    const exists = this.myCourses.find(c => c.id.toLowerCase() === courseId.toLowerCase());
    if (exists) return;
    const found = this.availableCourses.find(c => c.id.toLowerCase() === courseId.toLowerCase());
    if (!found) return;

    this.myCourses = [...this.myCourses, found];
    this.notify();
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

        const uid = (typeof window !== 'undefined') ? localStorage.getItem('current_user_id') : null;
        if (uid) {
          localStorage.setItem(`u:${uid}:myCourses:v1`, JSON.stringify(this.myCourses));
        }
        await this.syncDeadlinesFromCourses();
        if (uid) {
          localStorage.setItem(`u:${uid}:deadlines:v1`, JSON.stringify(this.deadlines));
        }
        this.notify();
      } catch (error) {
        console.warn('Failed to add course via API:', error);

        await this.syncDeadlinesFromCourses();
        const uid = (typeof window !== 'undefined') ? localStorage.getItem('current_user_id') : null;
        if (uid) {
          localStorage.setItem(`u:${uid}:myCourses:v1`, JSON.stringify(this.myCourses));
          localStorage.setItem(`u:${uid}:deadlines:v1`, JSON.stringify(this.deadlines));
        }
        this.notify();
      }
    })();
  }

  async removeCourse(courseId: string) {
  await apiService.removeCourse(courseId);  // 1) delete backend data

  const uid = localStorage.getItem('current_user_id');

  // 2) delete localstorage
  delete this.tasksByCourse[courseId];
  this.myCourses = this.myCourses.filter(c => c.id !== courseId);

  if (uid) {
    localStorage.setItem(`u:${uid}:myCourses:v1`, JSON.stringify(this.myCourses));
    localStorage.removeItem(`u:${uid}:ai-web-weekly-plans`);
  }

  try {
    await this.syncDeadlinesFromCourses();
  } catch (e) {
    console.warn('syncDeadlinesFromCourses failed after remove:', e);
  } finally {
    if (uid) {
      localStorage.setItem(`u:${uid}:deadlines:v1`, JSON.stringify(this.deadlines));
    }
  }

  this.notify();
}

  // Load tasks on demand (first retrieved and cached from the backend)
  async getCourseTasksAsync(courseId: string): Promise<Task[]> {
    if (!this.tasksByCourse[courseId]) {
      const apiTasks = await apiService.getCourseTasks(courseId);
      this.tasksByCourse[courseId] = apiTasks.map(t => ({
        id: String(t.id),
        title: t.title,
        deadline: t.deadline,
        brief: t.brief,
        percentContribution: (t as any).percent_contribution ?? t.percentContribution,
        url: (t as any).url ?? null, 
      }));
      
      await this.syncDeadlinesFromCourses();
      this.notify();
    }
    return this.tasksByCourse[courseId];
  }

  // Synchronize deadlines (dependent on tasks cache)

  private async syncDeadlinesFromCourses() {
    const list: Deadline[] = [];
    // Ensure task caching for each course

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
    const firstDash = id.indexOf('-');
    const taskId = firstDash >= 0 ? id.substring(firstDash + 1) : id;
    try {
      if (taskId) {
        await apiService.updateTaskProgress(taskId, progress);
      }
    } catch (e) {
      console.warn('updateTaskProgress failed, continue locally:', e);
    }

    // 1) Write memory mapping
    this.progressByDeadline[id] = progress;

    // 2) If there are corresponding items in the existing deadlines, update them directly on-site; Otherwise, rebuild the deadlines to bring in the latest progress

    const idx = this.deadlines.findIndex(d => d.id === id);
    if (idx !== -1) {
      this.deadlines[idx] = { ...this.deadlines[idx], progress };
    } else {
      await this.syncDeadlinesFromCourses();
    }

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

  // Calculate the overall progress of the course (weighted by task weight)

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