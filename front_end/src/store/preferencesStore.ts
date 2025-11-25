import { coursesStore } from './coursesStore';
import { apiService } from '../services/api';

export interface Preferences {
  dailyHours: number;          // hours per day
  weeklyStudyDays: number;     // days per week
  avoidDays: string[];         // avoid study days ['Sat','Sun']
  saveAsDefault: boolean;      // set as default or not
  description?: string;        
}

export interface PlanItem {
  id: string;           // `${courseId}-${taskId}` 
  courseId: string;
  courseTitle: string;  // course code + task title (deadline title)
  partTitle: string;
  minutes: number;
  date: string;         // YYYY-MM-DD
  color: string;
  completed?: boolean;
  partIndex?: number;
  partsCount?: number;
}

export interface WeeklyPlan {
  [weekOffset: number]: PlanItem[];  // store the plan base on weekoffset
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
  private weeklyPlans: WeeklyPlan = {};  
  private listeners: Listener[] = [];


  constructor() {

  }

  // load pref
  async loadPreferencesFromAPI(): Promise<void> {
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
    }
  }

  // save pref to db
  private async savePreferencesToAPI(): Promise<void> {
    try {
      await apiService.savePreferences(this.prefs);
    } catch (error) {
      console.warn('Failed to save preferences to API, falling back to localStorage:', error);
      this.savePreferences();
    }
  }

  // save pref to local storage
  private savePreferences() {
    try {
      const uid = localStorage.getItem('current_user_id');
      if (!uid) {
      console.warn('No current user ID found when saving preferences.');
      return;
    }
      const key = `u:${uid}:ai-web-preferences`;
      localStorage.setItem(key, JSON.stringify(this.prefs));
    } catch (error) {
      console.warn('Failed to save preferences to localStorage:', error);
    }
  }

  loadWeeklyPlans(uid?: string) {
  try {
    const userId = uid || localStorage.getItem('current_user_id');
    if (!userId) {
      console.warn('No user ID provided when loading weekly plans.');
      this.weeklyPlans = {};
      return;
    }
    const key = `u:${userId}:ai-web-weekly-plans`;
    const raw = localStorage.getItem(key);
    this.weeklyPlans = raw ? JSON.parse(raw) : {};
    this.notify();
  } catch (e) {
    console.warn('Failed to load weekly plans from localStorage:', e);
    this.weeklyPlans = {};
  }
}

async loadAllPlansSmart(uid: string): Promise<Record<string, PlanItem[]>> {
  type WeeklyPlansMap = Record<string, PlanItem[]>;

  const key = `u:${uid}:ai-web-weekly-plans`;

  // 1) read local storage
  const raw = localStorage.getItem(key);
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as WeeklyPlansMap;     
      this.weeklyPlans = parsed as unknown as WeeklyPlan;   
      this.notify?.();
      return parsed;                                        
    } catch {}
  }

  // 2) not in localstorage → backend db
  const map = (await apiService.getAllWeeklyPlans()) as WeeklyPlansMap;

  this.weeklyPlans = map as unknown as WeeklyPlan;         
  localStorage.setItem(key, JSON.stringify(map));
  this.notify?.();
  return map;                                             
}

  
private async saveWeeklyPlans() {
  try {
    const uid = localStorage.getItem('current_user_id');
    if (!uid) {
      console.warn('No current user ID found when saving weekly plans.');
      return;
    }
    const key = `u:${uid}:ai-web-weekly-plans`;
    console.log('[saveWeeklyPlans] weeklyPlans =', this.weeklyPlans);
    localStorage.setItem(key, JSON.stringify(this.weeklyPlans));
    const result = await apiService.saveWeeklyPlansToServer(this.weeklyPlans as Record<string, any[]>);

    if (!result.ok) {
      console.warn('[saveWeeklyPlans] ❌ Failed to sync to DB:', result.error);
    } else {
      console.log('[saveWeeklyPlans] ✅ Synced to DB successfully:', result);
    }

  } catch (error) {
    console.warn('Failed to save weekly plans to localStorage or DB:', error);
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
    return { ...this.prefs, avoidDays: [...this.prefs.avoidDays] };
  }

  async setPreferences(next: Partial<Preferences>) {
    this.prefs = {
      ...this.prefs,
      ...next,
      avoidDays: next.avoidDays ? [...next.avoidDays] : this.prefs.avoidDays
    };
    return this.savePreferencesToAPI().then(() => {
    this.notify();
  });
  }

  // get specific week's plan
  getWeeklyPlan(weekOffset: number): PlanItem[] {
    return this.weeklyPlans[weekOffset] || [];
  }

  // set specific week's plan
  setWeeklyPlan(weekOffset: number, plan: PlanItem[]) {
    this.weeklyPlans[weekOffset] = plan;
    this.saveWeeklyPlans();
    this.notify();
  }

  // clear plans
  clearWeeklyPlans() {
    this.weeklyPlans = {};
    this.saveWeeklyPlans();
    this.notify();
  }


  getCurrentWeeklyPlan(): PlanItem[] {
    return this.getWeeklyPlan(0);
  }

  // validate pref
  validatePreferences(preferences: Preferences): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // hours/day
    if (preferences.dailyHours < 1 || preferences.dailyHours > 12) {
      errors.push('Daily study hours must be between 1 and 12.');
    }
    
    // days/week
    if (preferences.weeklyStudyDays < 1 || preferences.weeklyStudyDays > 7) {
      errors.push('Weekly study days must be between 1 and 7.');
    }
    
    // Verify that the number of days avoided does not conflict
    const allDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const availableDays = allDays.filter(day => !preferences.avoidDays.includes(day));
    
    if (availableDays.length < preferences.weeklyStudyDays) {
      errors.push(`Too many avoid days selected — remaining available days (${availableDays.length}) are fewer than the desired weekly study days (${preferences.weeklyStudyDays}).`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Applying constraints to learning plans

  applyConstraints(preferences: Preferences, planItems: PlanItem[]): PlanItem[] {
    const dailyMinutesLimit = preferences.dailyHours * 60;
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // Group plan items by date

    const dailyPlans: { [date: string]: PlanItem[] } = {};
    planItems.forEach(item => {
      if (!dailyPlans[item.date]) {
        dailyPlans[item.date] = [];
      }
      dailyPlans[item.date].push(item);
    });
    
    // check daily studying hours
    const constrainedPlan: PlanItem[] = [];
    
    Object.entries(dailyPlans).forEach(([date, items]) => {
      const studyDate = new Date(date);
      const dayName = dayNames[studyDate.getDay()];
      
      // Check if it is within the number of days to avoid

      if (preferences.avoidDays.includes(dayName)) {
        console.warn(`Plan items are assigned to avoid days: ${date} (${dayName})`);
        return; 
      }
      
      // Calculate the total duration of the day
      const totalMinutes = items.reduce((sum, item) => sum + item.minutes, 0);
      if (totalMinutes > dailyMinutesLimit) {
        // If timeout occurs, reassign according to priority
        const sortedItems = [...items].sort((a, b) => {
          // Simple priority sorting: Sort by course ID and task ID
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

  //Generate learning plan (using AI functionality)
  async generateWeeklyPlan(): Promise<PlanItem[]> {
    const preferences = this.getPreferences();
    console.log('[DEBUG] get current pref:', preferences);
    const validation = this.validatePreferences(preferences);
    console.log('[DEBUG] validation res:', validation);
    if (!validation.isValid) {
      console.error('fail to validate:', validation.errors);
      return [];
    }
    else{
      console.log('validate pass:', preferences);
    }
    
    const myCourses = await apiService.getUserCourses();
    console.log('courses list:', myCourses);

    //const myCourses = coursesStore.myCourses;
    const planItems: PlanItem[] = [];
    
    // no course , no plan
    if (myCourses.length === 0) {
      return [];
    }
    

    const now = new Date();
    const day = now.getDay() || 7; 
    const currentMonday = new Date(now);
    currentMonday.setDate(now.getDate() - (day - 1));
    
    //Calculate the available learning days (excluding avoidance days and limiting the number of learning days per week)
    const availableDays = this.getAvailableStudyDays(preferences, currentMonday);
    
    // collect all tasks
    const allTasks: Array<{courseId: string, taskId: string, title: string, deadline: Date, color: string, priority: number, totalMinutes: number, parts: Array<{title: string, minutes: number}>}> = [];
    
    myCourses.forEach(course => {
      const tasks = coursesStore.getCourseTasks(course.id);
      console.log('tasks:',tasks)
      tasks.forEach(task => {
        // Calculate task priority (based on deadline)
        const deadline = new Date(task.deadline);
        const daysUntilDeadline = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        const priority = daysUntilDeadline <= 7 ? 1 : daysUntilDeadline <= 14 ? 2 : 3;
        
        // Using AI to intelligently split tasks
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
    
    // Sort by priority and deadline (high priority and near deadline priority)
    allTasks.sort((a, b) => {
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }
      return a.deadline.getTime() - b.deadline.getTime();
    });
    
    const dailyMinutesLimit = preferences.dailyHours * 60;
    const dayAssignments: {[date: string]: {totalMinutes: number, tasks: Array<{task: any, partIndex: number, part: any}>}} = {};
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    allTasks.forEach(task => {
      task.parts.forEach((part, partIndex) => {
        let remaining = part.minutes;
        
        // Prioritize allocation before the deadline
        for (let i = 0; i < availableDays.length && remaining > 0; i++) {
          const studyDate = availableDays[i];
          const dateStr = studyDate.toISOString().split('T')[0];
          
          //Allocate only on or before the deadline. If there are still leftovers, attempts will be made after the deadline until the latest deadline
          if (studyDate > task.deadline) break;
          
          const currentAssignment = dayAssignments[dateStr] || { totalMinutes: 0, tasks: [] };
          const dayName = dayNames[studyDate.getDay()];
          if (preferences.avoidDays.includes(dayName)) continue;
          const capacity = Math.max(0, dailyMinutesLimit - currentAssignment.totalMinutes);
          if (capacity <= 0) continue;
          
          const chunk = Math.min(remaining, capacity);
          
          // Initialize daily records
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
          
          // update today's load
          dayAssignments[dateStr].totalMinutes += chunk;
          dayAssignments[dateStr].tasks.push({ task, partIndex, part });
          
          remaining -= chunk;
        }
        
        //if there is still surplus, it is allowed to continue allocation after the deadline (until the latest global deadline), so that the global plan covers multiple weeks
        if (remaining > 0) {
          for (let i = 0; i < availableDays.length && remaining > 0; i++) {
            const studyDate = availableDays[i];
            const dateStr = studyDate.toISOString().split('T')[0];
            
            const currentAssignment = dayAssignments[dateStr] || { totalMinutes: 0, tasks: [] };
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
    
    // Apply constraints for final validation and adjustment
    const constrainedPlan = this.applyConstraints(preferences, planItems);
    return constrainedPlan;
  }
  
  private getAvailableStudyDays(preferences: Preferences, startDate: Date): Date[] {
    const availableDays: Date[] = [];
    const avoidSet = new Set(preferences.avoidDays);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // Obtain the latest deadline for all courses
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
    
    // Calculate the number of days to be generated (from startDate to the latest deadline)
    const daysNeeded = Math.ceil((latestDeadline.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    
    // Group by week to ensure that the number of study days per week does not exceed the specified limit
    const weeks: Date[][] = [];
    let currentWeek: Date[] = [];
    
    for (let i = 0; i < daysNeeded; i++) {
      // Create a new date object to avoid modifying the original startDate
      const studyDate = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000);
      const dayIndex = studyDate.getDay(); // 0-6 (sun=0, mon=1, ..., sat=6)
      const dayName = dayNames[dayIndex];
      

      if (!avoidSet.has(dayName)) {
        currentWeek.push(studyDate);
      }
      
      // If it is Saturday or the last day, end the current week and apply the weeklyStudyDays restriction

      if (dayIndex === 6 || i === daysNeeded - 1) {
        if (currentWeek.length > 0) {
          // Apply weeklyStudyDays restriction: select the top N available days (sorted by date)

          const sortedWeek = [...currentWeek].sort((a, b) => a.getTime() - b.getTime());
          const limitedWeek = sortedWeek.slice(0, preferences.weeklyStudyDays);
          weeks.push(limitedWeek);
        }
        currentWeek = [];
      }
    }
    
    // Merge the available days of all weeks
    weeks.forEach(week => {
      availableDays.push(...week);
    });
    
    // Sort by date
    availableDays.sort((a, b) => a.getTime() - b.getTime());
    
    return availableDays;
  }
  
  // Using AI to intelligently generate task splitting
  private generateAITaskParts(task: {courseId: string, taskId: string, title: string, deadline: Date, color: string, priority: number}): Array<{title: string, minutes: number}> {
    // Intelligent splitting based on task type and priority
    const baseMinutes = 30; // Adjust to a more easily testable base duration
    
    // Adjust task complexity based on priority
    const complexityMultiplier = task.priority === 1 ? 1.3 : task.priority === 2 ? 1.1 : 0.9;
    
    // Analyze task types
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
  
  // Analyze task types
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