// src/utils/overdueUtils.ts
//the logic of these function is outdated and useless,plz skip

export function getTasksOfDate(targetDateStr: string) {
  const uid = localStorage.getItem('current_user_id');
  if (!uid) return [];

  let raw: string | null = null;
  try {
    raw = localStorage.getItem(`u:${uid}:ai-web-weekly-plans`);
  } catch {
    return [];
  }
  if (!raw) return [];

  let allWeeks: Record<string, any[]> = {};
  try {
    allWeeks = JSON.parse(raw);
  } catch {
    return [];
  }

  const allItems = (Object.values(allWeeks) as any[]).flat();

  return allItems.filter(
    (it: any) => String(it?.date ?? '').slice(0, 10) === targetDateStr
  );
}


export function extractTaskId(courseId: string, fullId: string) {
  const prefix = `${courseId}-`;
  let s = String(fullId || '');
  if (s.startsWith(prefix)) s = s.slice(prefix.length);
  return s.replace(/-\d+$/, '');
}

export function isUncompleted(x: any) {
  return x?.completed !== true;
}

export function analyzeOverdue(tasksOfDay: any[]) {
  if (!Array.isArray(tasksOfDay) || tasksOfDay.length === 0) {
    return { overdueTasks: [], isWholeDayOverdue: false };
  }


  const grouped = new Map<
    string,
    { courseId: string; taskId: string; parts: any[] }
  >();

  for (const it of tasksOfDay) {
    const courseId = String(it?.courseId ?? '');
    const taskId = extractTaskId(courseId, String(it?.id ?? ''));
    const key = `${courseId}::${taskId}`; 
    const entry = grouped.get(key) ?? { courseId, taskId, parts: [] };
    entry.parts.push(it);
    grouped.set(key, entry);
  }

  const overdueTasks: { courseId: string; taskId: string }[] = [];
  for (const { courseId, taskId, parts } of grouped.values()) {
    if (parts.length > 0 && parts.every(isUncompleted)) {
      overdueTasks.push({ courseId, taskId });
    }
  }

  const isWholeDayOverdue =
    tasksOfDay.length > 0 && tasksOfDay.every(isUncompleted);

  return { overdueTasks, isWholeDayOverdue };
}
