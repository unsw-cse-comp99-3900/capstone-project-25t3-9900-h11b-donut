// src/utils/overdueUtils.ts

/** 解析出某天所有任务（本地 weekly-plans 中的 date 精确匹配 YYYY-MM-DD） */
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
  // 仅比较前 10 位日期（防止含时区字符串失配）
  return allItems.filter(
    (it: any) => String(it?.date ?? '').slice(0, 10) === targetDateStr
  );
}

/** 从 fullId 提取 taskId，例如 "COMP9900-540003-1" -> "540003" */
export function extractTaskId(courseId: string, fullId: string) {
  const prefix = `${courseId}-`;
  let s = String(fullId || '');
  if (s.startsWith(prefix)) s = s.slice(prefix.length);
  return s.replace(/-\d+$/, ''); // 去掉结尾的 -1 / -2
}

/** 判断是否未完成（只有 true 才视为已完成） */
export function isUncompleted(x: any) {
  return x?.completed !== true;
}

export function analyzeOverdue(tasksOfDay: any[]) {
  if (!Array.isArray(tasksOfDay) || tasksOfDay.length === 0) {
    return { overdueTasks: [], isWholeDayOverdue: false };
  }

  // 按 (courseId, taskId) 分组
  const grouped = new Map<
    string,
    { courseId: string; taskId: string; parts: any[] }
  >();

  for (const it of tasksOfDay) {
    const courseId = String(it?.courseId ?? '');
    const taskId = extractTaskId(courseId, String(it?.id ?? ''));
    const key = `${courseId}::${taskId}`; // 用 :: 防止连字符冲突
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
