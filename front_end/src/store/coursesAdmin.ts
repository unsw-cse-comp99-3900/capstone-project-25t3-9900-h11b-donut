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
async getMyTasks(force = false) {
  if (this.loading && !force) return;
  this.loading = true;
  try {
    const adminId = localStorage.getItem('current_user_id');
    if (!adminId) {
      console.warn('[courseAdmin.getMyTasks] No admin_id found in localStorage');
      return;
    }

    // 确保课程数据已加载
    if (!this.all || this.all.length === 0) {
      await this.getMyCourses(true);
    }

    const allTasks: Record<string, any[]> = {};
    const countsByCourse: Record<string, number> = {}; 

    for (const course of this.all) {
      try {
        const tasks = await apiService.adminGetCourseTasks(course.id);
        const normalized = (tasks || []).map((t: any) => ({
          id: String(t.id),
          title: t.title ?? '',
          deadline: t.deadline ?? '',
          brief: t.brief ?? '',
          percentContribution: t.percent_contribution ?? 0,
        }));

        allTasks[course.id] = normalized;
        countsByCourse[course.id] = normalized.length; 

        // 每门课单独缓存
        localStorage.setItem(
          `admin:${adminId}:course_tasks_${course.id}`,
          JSON.stringify(normalized)
        );
      } catch (e) {
        console.error(`[courseAdmin.getMyTasks] failed for course ${course.id}:`, e);
        countsByCourse[course.id] = 0;
      }
    }

    localStorage.setItem(`admin:${adminId}:tasks`, JSON.stringify(allTasks));

    localStorage.setItem(
      `admin:${adminId}:tasks_counts_by_course`,
      JSON.stringify(countsByCourse)
    );

    const totalCount = Object.values(countsByCourse).reduce((sum, n) => sum + n, 0);
    localStorage.setItem(`admin:${adminId}:tasks_total_count`, String(totalCount));

    console.log(
      `[courseAdmin.getMyTasks] Saved all tasks for admin:${adminId}, total=${totalCount}`
    );
    this.notify();
  } catch (err) {
    console.error('[courseAdmin.getMyTasks] failed:', err);
  } finally {
    this.loading = false;
  }
}

async getMyMaterials(force = false) {
  if (this.loading && !force) return;
  this.loading = true;
  try {
    const adminId = localStorage.getItem('current_user_id');
    if (!adminId) return;

    if (!this.all || this.all.length === 0) {
      await this.getMyCourses(true); // 确保有课程列表
    }

    const allMaterials: Record<string, any[]> = {};

    for (const course of this.all) {
      const materials = await apiService.adminGetCourseMaterials(course.id);
      allMaterials[course.id] = (materials || []).map(m => ({
        id: String(m.id),
        title: m.title ?? '',
        url: m.url ?? '',
        description: m.description ?? '',  
      }));

      // 单课缓存（带 adminId）
      localStorage.setItem(
        `admin:${adminId}:course_materials_${course.id}`,
        JSON.stringify(allMaterials[course.id])
      );
    }

    // 汇总缓存
    localStorage.setItem(`admin:${adminId}:materials`, JSON.stringify(allMaterials));
    this.notify();
  } catch (err) {
    console.error('[courseAdmin.getMyMaterials] failed:', err);
  } finally {
    this.loading = false;
  }
}
async getMyQuestions(force = false) {
  if (this.loading && !force) return;
  this.loading = true;
  try {
    const adminId = localStorage.getItem('current_user_id');
    if (!adminId) return;

    if (!this.all || this.all.length === 0) {
      await this.getMyCourses(true);
    }

    const allQuestions: Record<string, any[]> = {};

    for (const course of this.all) {
      const qs = await apiService.adminGetCourseQuestions(course.id);
      
      allQuestions[course.id] = (qs || []).map(q => ({
        id: String(q.id),
        qtype: q.qtype,
        title: q.title ?? '',
        description: q.description ?? '',
        text: q.text ?? '',
        keywords: Array.isArray(q.keywords) ? q.keywords : [],
        choices: q.qtype === 'mcq' ? (q.choices || []) : undefined,
        answer: q.qtype === 'short' ? (q.answer ?? '') : undefined,
      }));

      localStorage.setItem(
        `admin:${adminId}:course_questions_${course.id}`,
        JSON.stringify(allQuestions[course.id])
      );
    }

    localStorage.setItem(`admin:${adminId}:questions`, JSON.stringify(allQuestions));
    this.notify();
  } catch (err) {
    console.error('[courseAdmin.getMyQuestions] failed:', err);
  } finally {
    this.loading = false;
  }
}
}

export const courseAdmin = new CourseAdminStore();
