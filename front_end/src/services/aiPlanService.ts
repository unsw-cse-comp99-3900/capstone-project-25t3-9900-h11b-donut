// src/services/aiPlanServices.ts
import type { PlanItem, WeeklyPlan } from '../store/preferencesStore';
import { coursesStore } from '../store/coursesStore';
import { apiService } from '../services/api';
import { aiChatService } from '../services/aiChatService';

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

      // 统一 ID 规范：`${courseId}-${taskId}`，确保可与 deadlines 的 `${courseId}-${taskId}` 匹配
      // 后端 AI 返回的 taskId 可能是 "COMP9900_3"，需要提取其中的数字 3 作为真实任务ID
      const numericIdMatch = String(taskId).match(/(\d+)$|_(\d+)$/);
      const normalizedTaskId = numericIdMatch ? (numericIdMatch[1] || numericIdMatch[2]) : String(taskId);

      const item: PlanItem = {
        id: `${courseId}-${normalizedTaskId}` + (Number.isFinite(partIndex as any) ? `-${partIndex}` : ''),
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
      
      // 调试信息：检查Gemini生成的标题
      console.log(`🔍 [mapAiPlanToWeeklyPlan] 任务: ${meta.taskTitle}, Part标题: ${b.title}`);
      console.log(`🎯 [GEMINI_TITLE_CHECK] 这是Gemini生成的特定标题: "${b.title}"`);

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
  
  console.log('🔍 fetchAndMapAiPlan 收到的数据:', aiPlan);
  console.log('🔍 AI计划的days数据:', aiPlan?.days);
  console.log('🔍 AI计划的aiSummary数据:', aiPlan?.aiSummary);
  
  // 检查AI计划数据
  if (!aiPlan || !aiPlan.ok) {
    throw new Error(aiPlan?.message || 'AI计划生成失败');
  }
  
  // aiPlan本身就是计划数据(api.ts已经返回了res.data)
  const planData = aiPlan;
  if (!planData || !planData.days) {
    throw new Error('后端返回空的AI计划数据。请检查网络连接或稍后重试。');
  }
  
  // 检查后端是否已经保存了计划（新的设计）
  if (aiPlan.saved) {
    console.log('✅ [fetchAndMapAiPlan] 后端已保存计划，计划ID:', aiPlan.plan_id);
    console.log('🤖 [fetchAndMapAiPlan] AI详细内容已包含在响应中');
  } else {
    console.log('⚠️ [fetchAndMapAiPlan] 后端未保存计划，使用旧逻辑');
    
    // 如果后端没有保存，则使用前端保存逻辑（兼容性）
    const weeklyPlan = mapAiPlanToWeeklyPlan(planData);
    const savePayload = {
      weeklyPlans: weeklyPlan,
      aiDetails: planData.aiDetails || null,
      generationReason: planData.aiDetails?.generationReason || '',
      generationTime: planData.aiDetails?.generationTime || null
    };
    
    const saveResult = await apiService.saveWeeklyPlansToServer(
      savePayload.weeklyPlans, 
      savePayload.aiDetails, 
      savePayload.generationReason, 
      savePayload.generationTime
    );
    
    if (!saveResult.ok) {
      console.error('❌ 学习计划保存失败:', saveResult.error);
      throw new Error(`学习计划保存失败: ${saveResult.error || '未知错误'}`);
    }
    
    console.log('✅ 学习计划已通过前端逻辑保存到数据库');
  }
  
  // 映射AI计划到周计划格式用于前端显示
  const weeklyPlan = mapAiPlanToWeeklyPlan(planData);
  console.log('🗓️ 映射后的周计划:', weeklyPlan);
  
  return weeklyPlan;
}
