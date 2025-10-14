import { coursesStore } from './coursesStore';
import { apiService } from '../services/api';

export interface Preferences {
  dailyHours: number;          // 每日学习时长（小时）
  weeklyStudyDays: number;     // 每周学习天数（1-7）
  avoidDays: string[];         // 需要规避的星期（如 ['Sat','Sun']）
  saveAsDefault: boolean;      // 是否保存为默认
  description?: string;        // 学生对课程基础的自我描述
}

export interface PlanItem {
  id: string;           // `${courseId}-${taskId}` 与 deadlines id 对齐（同一任务的多个 part 共享同一 id）
  courseId: string;
  courseTitle: string;  // course code + task title (deadline title)
  partTitle: string;
  minutes: number;
  date: string;         // YYYY-MM-DD
  color: string;
  completed?: boolean;
  // 新增：用于表示任务拆分的子步骤索引与总数
  partIndex?: number;
  partsCount?: number;
}

export interface WeeklyPlan {
  [weekOffset: number]: PlanItem[];  // 按周偏移存储计划
}

type Listener = () => void;

class PreferencesStore {
  private prefs: Preferences = {
    dailyHours: 2,
    weeklyStudyDays: 5,
    avoidDays: [],
    saveAsDefault: false,
    description: ''
  };
  private weeklyPlans: WeeklyPlan = {};  // 存储每周学习计划
  private listeners: Listener[] = [];


  constructor() {
    this.loadPreferencesFromAPI();
  }

  // 从API加载偏好设置
  private async loadPreferencesFromAPI(): Promise<void> {
    try {
      const preferences = await apiService.getPreferences();
      if (preferences) {
        this.prefs = {
          dailyHours: preferences.dailyHours || 2,
          weeklyStudyDays: preferences.weeklyStudyDays || 5,
          avoidDays: preferences.avoidDays || [],
          saveAsDefault: preferences.saveAsDefault || false,
          description: preferences.description || ''
        };

        this.notify();
      }
    } catch (error) {
      console.warn('Failed to load preferences from API, falling back to localStorage:', error);
      this.loadFromLocalStorage();
    }
  }

  // 保存偏好设置到API
  private async savePreferencesToAPI(): Promise<void> {
    try {
      await apiService.savePreferences(this.prefs);
    } catch (error) {
      console.warn('Failed to save preferences to API, falling back to localStorage:', error);
      this.savePreferences();
    }
  }



  // 从localStorage加载学习计划（备用方案）
  private loadFromLocalStorage(): void {
    try {
      const storedPrefs = localStorage.getItem('ai-web-preferences');
      if (storedPrefs) {
        const parsed = JSON.parse(storedPrefs);
        this.prefs = {
          dailyHours: parsed.dailyHours || 2,
          weeklyStudyDays: parsed.weeklyStudyDays || 5,
          avoidDays: parsed.avoidDays || [],
          saveAsDefault: parsed.saveAsDefault || false,
          description: parsed.description || ''
        };

      }
    } catch (error) {
      console.warn('Failed to load from localStorage:', error);
    }
  }



  // 保存偏好设置到localStorage,暂时没用上可能后面会用上？
  private savePreferences() {
    try {
      localStorage.setItem('ai-web-preferences', JSON.stringify(this.prefs));
    } catch (error) {
      console.warn('Failed to save preferences to localStorage:', error);
    }
  }

  // 保存学习计划到localStorage
  private saveWeeklyPlans() {
    try {
      localStorage.setItem('ai-web-weekly-plans', JSON.stringify(this.weeklyPlans));
    } catch (error) {
      console.warn('Failed to save weekly plans to localStorage:', error);
    }
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

  getPreferences(): Preferences {
    // 返回拷贝，避免外部直接修改内部状态
    return { ...this.prefs, avoidDays: [...this.prefs.avoidDays] };
  }

  async setPreferences(next: Partial<Preferences>) {
    this.prefs = {
      ...this.prefs,
      ...next,
      avoidDays: next.avoidDays ? [...next.avoidDays] : this.prefs.avoidDays
    };
    await this.savePreferencesToAPI();
    this.notify();
  }

  // 获取指定周的学习计划
  getWeeklyPlan(weekOffset: number): PlanItem[] {
    return this.weeklyPlans[weekOffset] || [];
  }

  // 设置指定周的学习计划
  setWeeklyPlan(weekOffset: number, plan: PlanItem[]) {
    this.weeklyPlans[weekOffset] = plan;
    this.saveWeeklyPlans();
    this.notify();
  }

  // 清除所有学习计划数据
  clearWeeklyPlans() {
    this.weeklyPlans = {};
    this.saveWeeklyPlans();
    this.notify();
  }

  // 获取当前周的学习计划（默认本周）
  getCurrentWeeklyPlan(): PlanItem[] {
    return this.getWeeklyPlan(0);
  }

  // 验证偏好设置约束
  validatePreferences(preferences: Preferences): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // 验证每日学习时长
    if (preferences.dailyHours < 1 || preferences.dailyHours > 12) {
      errors.push('每日学习时长必须在1-12小时之间');
    }
    
    // 验证每周学习天数
    if (preferences.weeklyStudyDays < 1 || preferences.weeklyStudyDays > 7) {
      errors.push('每周学习天数必须在1-7天之间');
    }
    
    // 验证避免天数不冲突
    const allDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const availableDays = allDays.filter(day => !preferences.avoidDays.includes(day));
    
    if (availableDays.length < preferences.weeklyStudyDays) {
      errors.push(`选择的避免天数过多，剩余可用天数(${availableDays.length})少于每周学习天数(${preferences.weeklyStudyDays})`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // 应用约束条件到学习计划
  applyConstraints(preferences: Preferences, planItems: PlanItem[]): PlanItem[] {
    const dailyMinutesLimit = preferences.dailyHours * 60;
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // 按日期分组计划项
    const dailyPlans: { [date: string]: PlanItem[] } = {};
    planItems.forEach(item => {
      if (!dailyPlans[item.date]) {
        dailyPlans[item.date] = [];
      }
      dailyPlans[item.date].push(item);
    });
    
    // 检查每日时长限制
    const constrainedPlan: PlanItem[] = [];
    
    Object.entries(dailyPlans).forEach(([date, items]) => {
      const studyDate = new Date(date);
      const dayName = dayNames[studyDate.getDay()];
      
      // 检查是否在避免天数中
      if (preferences.avoidDays.includes(dayName)) {
        console.warn(`计划项被分配到避免的天数: ${date} (${dayName})`);
        return; // 跳过这个日期的所有计划项
      }
      
      // 计算当日总时长
      const totalMinutes = items.reduce((sum, item) => sum + item.minutes, 0);
      
      if (totalMinutes > dailyMinutesLimit) {
        // 如果超时，按优先级重新分配
        const sortedItems = [...items].sort((a, b) => {
          // 简单的优先级排序：按课程ID和任务ID排序
          return a.id.localeCompare(b.id);
        });
        
        let remainingMinutes = dailyMinutesLimit;
        sortedItems.forEach(item => {
          if (remainingMinutes > 0) {
            const allocatedMinutes = Math.min(item.minutes, remainingMinutes);
            if (allocatedMinutes > 0) {
              constrainedPlan.push({
                ...item,
                minutes: allocatedMinutes
              });
              remainingMinutes -= allocatedMinutes;
            }
          }
        });
      } else {
        constrainedPlan.push(...items);
      }
    });
    
    return constrainedPlan;
  }

  // 生成学习计划（使用AI功能）
  async generateWeeklyPlan(): Promise<PlanItem[]> {
    const preferences = this.getPreferences();
    
    // 验证偏好设置
    const validation = this.validatePreferences(preferences);
    if (!validation.isValid) {
      console.error('偏好设置验证失败:', validation.errors);
      return [];
    }
    else{
      console.log('偏好设置验证通过:', preferences);
    }
    
    // 获取用户的所有课程和任务
    const myCourses = await apiService.getUserCourses();
    console.log('🎓 课程信息列表:', myCourses);

    //const myCourses = coursesStore.myCourses;
    const planItems: PlanItem[] = [];
    
    // 如果没有课程，返回空计划
    if (myCourses.length === 0) {
      return [];
    }
    
    // 获取当前周的周一日期
    const now = new Date();
    const day = now.getDay() || 7; // 周一=1
    const currentMonday = new Date(now);
    currentMonday.setDate(now.getDate() - (day - 1));
    
    // 计算可用的学习天数（排除avoid days，并限制每周学习天数）
    const availableDays = this.getAvailableStudyDays(preferences, currentMonday);
    
    // 收集所有任务
    const allTasks: Array<{courseId: string, taskId: string, title: string, deadline: Date, color: string, priority: number, totalMinutes: number, parts: Array<{title: string, minutes: number}>}> = [];
    
    myCourses.forEach(course => {
      const tasks = coursesStore.getCourseTasks(course.id);
      tasks.forEach(task => {
        // 计算任务优先级（基于截止日期）
        const deadline = new Date(task.deadline);
        const daysUntilDeadline = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        const priority = daysUntilDeadline <= 7 ? 1 : daysUntilDeadline <= 14 ? 2 : 3;
        
        // 使用AI智能拆分任务
        const taskParts = this.generateAITaskParts({
          courseId: course.id,
          taskId: task.id,
          title: task.title,
          deadline: deadline,
          color: coursesStore.getColorByCourse(course.id),
          priority: priority
        });
        
        const totalMinutes = taskParts.reduce((sum, part) => sum + part.minutes, 0);
        
        allTasks.push({
          courseId: course.id,
          taskId: task.id,
          title: task.title,
          deadline: deadline,
          color: coursesStore.getColorByCourse(course.id),
          priority: priority,
          totalMinutes: totalMinutes,
          parts: taskParts
        });
      });
    });
    
    // 按优先级和截止日期排序（高优先级和近截止日期的优先）
    allTasks.sort((a, b) => {
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }
      return a.deadline.getTime() - b.deadline.getTime();
    });
    
    // 按天分配任务，严格应用daily hours限制
    const dailyMinutesLimit = preferences.dailyHours * 60;
    const dayAssignments: {[date: string]: {totalMinutes: number, tasks: Array<{task: any, partIndex: number, part: any}>}} = {};
    // 额外防护：在分配阶段再次检查避开日期
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // 为每个任务分配日期（严格应用每日时长限制、避免日与每周学习天数，并在必要时跨天拆分part）
    allTasks.forEach(task => {
      task.parts.forEach((part, partIndex) => {
        let remaining = part.minutes;
        
        // 优先在截止日期之前分配
        for (let i = 0; i < availableDays.length && remaining > 0; i++) {
          const studyDate = availableDays[i];
          const dateStr = studyDate.toISOString().split('T')[0];
          
          // 只在截止日期当天或之前分配，若仍有剩余，后续会尝试截止日之后直到最晚截止日期
          if (studyDate > task.deadline) break;
          
          const currentAssignment = dayAssignments[dateStr] || { totalMinutes: 0, tasks: [] };
          // 避开日期二次校验
          const dayName = dayNames[studyDate.getDay()];
          if (preferences.avoidDays.includes(dayName)) continue;
          const capacity = Math.max(0, dailyMinutesLimit - currentAssignment.totalMinutes);
          if (capacity <= 0) continue;
          
          const chunk = Math.min(remaining, capacity);
          
          // 初始化当日记录
          if (!dayAssignments[dateStr]) {
            dayAssignments[dateStr] = { totalMinutes: 0, tasks: [] };
          }
          
          // 创建计划项（可能是该part的一个切片）
          const planItem: PlanItem = {
            id: `${task.courseId}-${task.taskId}-${partIndex}`,
            courseId: task.courseId,
            courseTitle: `${task.courseId} - ${task.title}`,  // course code + task title
            partTitle: part.title,
            minutes: chunk,
            date: dateStr,
            color: task.color,
            completed: false,
            partIndex: partIndex + 1,
            partsCount: task.parts.length
          };
          planItems.push(planItem);
          
          // 更新当日负载
          dayAssignments[dateStr].totalMinutes += chunk;
          dayAssignments[dateStr].tasks.push({ task, partIndex, part });
          
          remaining -= chunk;
        }
        
        // 如果还有剩余，允许在截止日期之后继续分配（直到全局最新截止日期），以便全局计划覆盖多周
        if (remaining > 0) {
          for (let i = 0; i < availableDays.length && remaining > 0; i++) {
            const studyDate = availableDays[i];
            const dateStr = studyDate.toISOString().split('T')[0];
            
            const currentAssignment = dayAssignments[dateStr] || { totalMinutes: 0, tasks: [] };
            // 避开日期二次校验
            const dayName2 = dayNames[studyDate.getDay()];
            if (preferences.avoidDays.includes(dayName2)) continue;
            const capacity = Math.max(0, dailyMinutesLimit - currentAssignment.totalMinutes);
            if (capacity <= 0) continue;
            
            const chunk = Math.min(remaining, capacity);
            
            if (!dayAssignments[dateStr]) {
              dayAssignments[dateStr] = { totalMinutes: 0, tasks: [] };
            }
            
            const planItem: PlanItem = {
              id: `${task.courseId}-${task.taskId}-${partIndex}`,
              courseId: task.courseId,
              courseTitle: `${task.courseId} - ${task.title}`,  // course code + task title
              partTitle: part.title,
              minutes: chunk,
              date: dateStr,
              color: task.color,
              completed: false,
              partIndex: partIndex + 1,
              partsCount: task.parts.length
            };
            planItems.push(planItem);
            
            dayAssignments[dateStr].totalMinutes += chunk;
            dayAssignments[dateStr].tasks.push({ task, partIndex, part });
            
            remaining -= chunk;
          }
        }
      });
    });
    
    // 应用约束条件进行最终验证和调整
    const constrainedPlan = this.applyConstraints(preferences, planItems);
    return constrainedPlan;
  }
  
  // 获取可用的学习天数（基于最晚截止日期，应用avoid days和weekly study days限制）
  private getAvailableStudyDays(preferences: Preferences, startDate: Date): Date[] {
    const availableDays: Date[] = [];
    const avoidSet = new Set(preferences.avoidDays);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // 获取所有课程的最晚截止日期
    const myCourses = coursesStore.myCourses;
    let latestDeadline = new Date(startDate);
    
    myCourses.forEach(course => {
      const tasks = coursesStore.getCourseTasks(course.id);
      tasks.forEach(task => {
        const deadline = new Date(task.deadline);
        if (deadline > latestDeadline) {
          latestDeadline = deadline;
        }
      });
    });
    
    // 计算需要生成的天数（从startDate到最晚截止日期）
    const daysNeeded = Math.ceil((latestDeadline.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    
    // 按周分组，确保每周不超过指定的学习天数
    const weeks: Date[][] = [];
    let currentWeek: Date[] = [];
    
    for (let i = 0; i < daysNeeded; i++) {
      // 创建新的日期对象，避免修改原始startDate
      const studyDate = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000);
      const dayIndex = studyDate.getDay(); // 0-6 (周日=0, 周一=1, ..., 周六=6)
      const dayName = dayNames[dayIndex];
      
      // 检查是否在avoid days中
      if (!avoidSet.has(dayName)) {
        currentWeek.push(studyDate);
      }
      
      // 如果是周六或最后一天，结束当前周并应用weeklyStudyDays限制
      if (dayIndex === 6 || i === daysNeeded - 1) {
        if (currentWeek.length > 0) {
          // 应用weeklyStudyDays限制：取前N个可用天数（按日期排序）
          const sortedWeek = [...currentWeek].sort((a, b) => a.getTime() - b.getTime());
          const limitedWeek = sortedWeek.slice(0, preferences.weeklyStudyDays);
          weeks.push(limitedWeek);
        }
        currentWeek = [];
      }
    }
    
    // 合并所有周的可用天数
    weeks.forEach(week => {
      availableDays.push(...week);
    });
    
    // 按日期排序
    availableDays.sort((a, b) => a.getTime() - b.getTime());
    
    return availableDays;
  }
  
  // 使用AI智能生成任务拆分
  private generateAITaskParts(task: {courseId: string, taskId: string, title: string, deadline: Date, color: string, priority: number}): Array<{title: string, minutes: number}> {
    // 基于任务类型和优先级智能拆分
    const baseMinutes = 30; // 调整为更易测试的基础时长
    
    // 根据优先级调整任务复杂度
    const complexityMultiplier = task.priority === 1 ? 1.3 : task.priority === 2 ? 1.1 : 0.9;
    
    // 分析任务类型
    const taskType = this.analyzeTaskType(task.title);
    
    switch (taskType) {
      case 'coding':
        return [
          { title: `Part 1 - Analysis`, minutes: Math.round(baseMinutes * 0.8 * complexityMultiplier) },
          { title: `Part 2 - Design`, minutes: Math.round(baseMinutes * 1.2 * complexityMultiplier) },
          { title: `Part 3 - Implement`, minutes: Math.round(baseMinutes * 2.0 * complexityMultiplier) },
          { title: `Part 4 - Testing`, minutes: Math.round(baseMinutes * 1.0 * complexityMultiplier) },
          { title: `Part 5 - Optimization`, minutes: Math.round(baseMinutes * 0.8 * complexityMultiplier) }
        ];
      
      case 'research':
        return [
          { title: `Part 1 - Background Study`, minutes: Math.round(baseMinutes * 1.5 * complexityMultiplier) },
          { title: `Part 2 - Data Collection`, minutes: Math.round(baseMinutes * 1.0 * complexityMultiplier) },
          { title: `Part 3 - Analysis`, minutes: Math.round(baseMinutes * 1.8 * complexityMultiplier) },
          { title: `Part 4 - Report Writing`, minutes: Math.round(baseMinutes * 1.5 * complexityMultiplier) }
        ];
      
      case 'writing':
        return [
          { title: `Part 1 - Outline`, minutes: Math.round(baseMinutes * 0.6 * complexityMultiplier) },
          { title: `Part 2 - Draft`, minutes: Math.round(baseMinutes * 2.0 * complexityMultiplier) },
          { title: `Part 3 - Revision`, minutes: Math.round(baseMinutes * 1.2 * complexityMultiplier) },
          { title: `Part 4 - Polishing`, minutes: Math.round(baseMinutes * 0.8 * complexityMultiplier) }
        ];
      
      default:
        return [
          { title: `Part 1 - Preparation`, minutes: Math.round(baseMinutes * 0.8 * complexityMultiplier) },
          { title: `Part 2 - Execution`, minutes: Math.round(baseMinutes * 1.5 * complexityMultiplier) },
          { title: `Part 3 - Review`, minutes: Math.round(baseMinutes * 0.7 * complexityMultiplier) }
        ];
    }
  }
  
  // 分析任务类型
  private analyzeTaskType(title: string): string {
    const lowerTitle = title.toLowerCase();
    
    if (lowerTitle.includes('code') || lowerTitle.includes('program') || lowerTitle.includes('develop') || lowerTitle.includes('implement')) {
      return 'coding';
    }
    if (lowerTitle.includes('research') || lowerTitle.includes('study') || lowerTitle.includes('analyze') || lowerTitle.includes('survey')) {
      return 'research';
    }
    if (lowerTitle.includes('write') || lowerTitle.includes('essay') || lowerTitle.includes('report') || lowerTitle.includes('paper')) {
      return 'writing';
    }
    
    return 'general';
  }
}

export const preferencesStore = new PreferencesStore();