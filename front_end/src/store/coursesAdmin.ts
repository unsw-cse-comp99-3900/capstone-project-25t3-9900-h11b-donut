// src/stores/courseAdmin.ts
import { apiService } from '../services/api';

export type AdminCourse = {
  id: string;
  title: string;
  desc: string;
  illustration: 'orange' | 'student' | 'admin';
};

type Listener = () => void;

class CourseAdminStore {
  all: AdminCourse[] = [];
  private listeners: Listener[] = [];
  private loading = false;
  subscribe(fn: Listener) { this.listeners.push(fn); return () => this.listeners = this.listeners.filter(l => l !== fn); }
  private notify() { this.listeners.forEach(l => l()); }

  async getMyCourses(force = false) {
    if (this.loading && !force) return;
    this.loading = true;
    try {
        const list = await apiService.adminGetMyCourses();

        this.all = (list || []).map((c: any,idx: number) => ({
            id: String(c.code),
            title: c.title ?? '',
            desc: c.description ?? '',
            illustration: (['orange','student','admin'].includes(c.illustration)
                ? c.illustration
                : 'admin') as 'orange' | 'student' | 'admin',
            studentCount: c.student_count ?? 0,
            illustrationIndex: idx % 4,
            }));
            const adminId = localStorage.getItem('current_user_id');
            
            if (adminId) {
            localStorage.setItem(`admin:${adminId}:courses`, JSON.stringify(this.all));
            }
            this.notify();
    } catch (err) {
        console.error('[courseAdmin.getMyCourses] failed:', err);
    } finally {
        this.loading = false;
  }
}
}

export const courseAdmin = new CourseAdminStore();
