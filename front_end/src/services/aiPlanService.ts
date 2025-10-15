// src/services/aiPlanServices.ts
import type { PlanItem, WeeklyPlan } from '../store/preferencesStore';
import { coursesStore } from '../store/coursesStore';
import { apiService } from '../services/api';

// —— 工具：给定日期回到该周周一（本地时区）——
function weekMonday(d: Date) {
  const dd = new Date(d);
  const wd = dd.getDay() || 7;           // Sun=0 -> 7
  dd.setHours(0, 0, 0, 0);
  dd.setDate(dd.getDate() - (wd - 1));   // 回到周一
  return dd;
}

// —— 工具：计算两日期所在“周一”的周偏移差（整数）——
function weekDiff(a: Date, b: Date) {
  const msPerWeek = 7 * 24 * 60 * 60 * 1000;
  return Math.round((weekMonday(a).getTime() - weekMonday(b).getTime()) / msPerWeek);
}

/**
 * 核心：把后端的 aiPlan 映射为前端 WeeklyPlan（以 weekOffset 为 key）
 * 期望 aiPlan.days 结构：[{ date: 'YYYY-MM-DD', blocks: [{taskId, partId, title, minutes, ...}] }]
 * 期望 aiPlan.aiSummary.tasks：[{ taskId, taskTitle, parts: [...] }]
 */
export function mapAiPlanToWeeklyPlan(aiPlan: any): WeeklyPlan {
  const weekly: WeeklyPlan = {};
  if (!aiPlan || !Array.isArray(aiPlan.days)) return weekly;

  // 任务元信息索引 (taskId -> { taskTitle, partsCount })
  const metaByTaskId: Record<string, { taskTitle: string; partsCount: number }> = {};
  if (aiPlan.aiSummary?.tasks) {
    for (const t of aiPlan.aiSummary.tasks) {
      metaByTaskId[t.taskId] = {
        taskTitle: t.taskTitle || t.taskId,
        partsCount: Array.isArray(t.parts) ? t.parts.length : 0,
      };
    }
  }

  // 以后端返回的 weekStart 为基准周；否则用第一天的周一；再不行用今天的周一
  const baseWeekStart =
    aiPlan.weekStart
      ? weekMonday(new Date(aiPlan.weekStart))
      : (aiPlan.days.length
          ? weekMonday(new Date(aiPlan.days[0].date))
          : weekMonday(new Date()));

  // 遍历每天与其 blocks，生成 PlanItem 并按周偏移归类
  for (const day of aiPlan.days) {
    const dateStr: string = day.date;     // 已是 'YYYY-MM-DD'
    const dateObj = new Date(dateStr);
    const offset = weekDiff(dateObj, baseWeekStart);
    if (!weekly[offset]) weekly[offset] = [];

    for (const b of (day.blocks || [])) {
      const taskId: string = b.taskId;                     // 如 "COMP9900_3"
      const courseId = taskId.split('_')[0] || taskId;     // "COMP9900"
      const meta = metaByTaskId[taskId] || { taskTitle: taskId, partsCount: 0 };

      // 从 partId 提取序号（p1 -> 1）
      const maybeIndex = parseInt(String(b.partId).replace(/\D+/g, ''), 10);
      const partIndex = Number.isFinite(maybeIndex) ? maybeIndex : undefined;

      const item: PlanItem = {
        // 你定义里说“同一任务多个 part 共享同一 id”，保持一致：
        id: `${courseId}-${taskId}`,
        courseId,
        courseTitle: meta.taskTitle,        // 例如 "COMP9900 - Final Presentation"
        partTitle: b.title,                 // "Part 1" 等
        minutes: b.minutes,                 // 60
        date: dateStr,                      // 直接用后端给的 YYYY-MM-DD，避免时区坑
        color: coursesStore.getColorByCourse(courseId) || '#888',
        completed: false,
        partIndex,
        partsCount: meta.partsCount,
      };

      weekly[offset].push(item);
    }
  }

  return weekly;
}

/**
 * 一步到位：请求后端 AI 计划 → 映射为 WeeklyPlan 返回
 * 失败时抛错，外层可选择 fallback 到本地 generateWeeklyPlan()
 */
export async function fetchAndMapAiPlan(): Promise<WeeklyPlan> {
  const aiPlan = await apiService.generateAIPlan();
  // 这里可以根据 aiPlan.ok / message 做一下校验
  return mapAiPlanToWeeklyPlan(aiPlan);
}
