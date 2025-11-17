import { getTasksOfDate, analyzeOverdue } from './overdueUtils';

// 本地时区下格式化 YYYY-MM-DD
function formatLocalDate(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// 取本地时区的“昨天” YYYY-MM-DD
function getYesterdayLocalDateStr() {
  const d = new Date();
  // 用本地日期减一天，避免 UTC 偏移
  d.setDate(d.getDate() - 1);
  return formatLocalDate(d);
}

// 简易 localStorage 锁：避免多标签页并发上报
function withLocalLock<T>(key: string, fn: () => Promise<T>, ttlMs = 10_000): Promise<T> {
  const now = Date.now();
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const { until } = JSON.parse(raw);
      if (typeof until === 'number' && until > now) {
        // 有有效锁，直接跳过
        return Promise.resolve(undefined as unknown as T);
      }
    }
  } catch { /* 忽略解析错误，继续加锁 */ }

  // 加锁
  localStorage.setItem(key, JSON.stringify({ until: now + ttlMs }));
  const release = () => localStorage.removeItem(key);

  return fn()
    .then((r) => { release(); return r; })
    .catch((e) => { release(); throw e; });
}

// 仅检查“昨天”的 overdue；若昨天没有 plan，则不汇报
export async function reportOverdueForYesterday() {
  const uid = localStorage.getItem('current_user_id');
  if (!uid) return;
  const yest = getYesterdayLocalDateStr(); // 使用本地时区的昨天
  const flagKey = `u:${uid}:overdue_reported_dates`;
  const lockKey = `u:${uid}:overdue_lock:${yest}`;
  
  // 读取已汇报日期列表（安全解析）
  let reported: string[] = [];
  try {
    reported = JSON.parse(localStorage.getItem(flagKey) || '[]') as string[];
    if (!Array.isArray(reported)) reported = [];
  } catch { reported = []; }
  // 已报告则返回（本地幂等）
  if (reported.includes(yest)) return;
  // 使用本地锁避免多标签页并发
  await withLocalLock(lockKey, async () => {
    // 再次检查，防止在等待锁期间已被其他标签页报告
    let recheck: string[] = [];
    try {
      recheck = JSON.parse(localStorage.getItem(flagKey) || '[]') as string[];
      if (!Array.isArray(recheck)) recheck = [];
    } catch { recheck = []; }
    if (recheck.includes(yest)) return;
    // 1) 取“昨天”的任务块；若没有 plan，直接跳过（不汇报、不打标）
    const items = getTasksOfDate(yest);
    
    if (!items || items.length === 0) return;
    
    const { overdueTasks, isWholeDayOverdue } = analyzeOverdue(items);

    // 2) 组装 payload（字段名确认与后端一致）
    const payload = {
      student_id: uid,
      date: yest,
      overdue_tasks: (overdueTasks || []).map((x: any) => ({
        course_code: x.courseId,
        task_id: x.taskId
      })),
      is_whole_day_overdue: !!isWholeDayOverdue
    };

    // 3) 上报
    const token = localStorage.getItem('auth_token') || '';
    let res: any = null;
    try {
      const r = await fetch('/api/overdue/report-day', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload)
      });
      // 仅 2xx 认为成功
      if (r.ok) res = await r.json().catch(() => ({}));
      else res = null;
    } catch {
      res = null; // 网络错误等
    }

    // 4) 成功后标记（仅在后端确认成功时）
    if (res && res.ok === true) {
      const next = Array.from(new Set([...(recheck.length ? recheck : reported), yest]));
      localStorage.setItem(flagKey, JSON.stringify(next));
      // 可选：console.log('[overdue:yesterday] reported OK:', res);
    }
  });
}
