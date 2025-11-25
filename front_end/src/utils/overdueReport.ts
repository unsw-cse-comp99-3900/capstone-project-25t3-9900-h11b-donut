//the logic of these function is outdated and useless,plz skip
import { getTasksOfDate, analyzeOverdue } from './overdueUtils';

function formatLocalDate(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getYesterdayLocalDateStr() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return formatLocalDate(d);
}

function withLocalLock<T>(key: string, fn: () => Promise<T>, ttlMs = 10_000): Promise<T> {
  const now = Date.now();
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const { until } = JSON.parse(raw);
      if (typeof until === 'number' && until > now) {
        return Promise.resolve(undefined as unknown as T);
      }
    }
  } catch { }

  localStorage.setItem(key, JSON.stringify({ until: now + ttlMs }));
  const release = () => localStorage.removeItem(key);

  return fn()
    .then((r) => { release(); return r; })
    .catch((e) => { release(); throw e; });
}

export async function reportOverdueForYesterday() {
  const uid = localStorage.getItem('current_user_id');
  if (!uid) return;
  const yest = getYesterdayLocalDateStr();
  const flagKey = `u:${uid}:overdue_reported_dates`;
  const lockKey = `u:${uid}:overdue_lock:${yest}`;
  

  let reported: string[] = [];
  try {
    reported = JSON.parse(localStorage.getItem(flagKey) || '[]') as string[];
    if (!Array.isArray(reported)) reported = [];
  } catch { reported = []; }

  if (reported.includes(yest)) return;

  await withLocalLock(lockKey, async () => {

    let recheck: string[] = [];
    try {
      recheck = JSON.parse(localStorage.getItem(flagKey) || '[]') as string[];
      if (!Array.isArray(recheck)) recheck = [];
    } catch { recheck = []; }
    if (recheck.includes(yest)) return;

    const items = getTasksOfDate(yest);
    
    if (!items || items.length === 0) return;
    
    const { overdueTasks, isWholeDayOverdue } = analyzeOverdue(items);

    const payload = {
      student_id: uid,
      date: yest,
      overdue_tasks: (overdueTasks || []).map((x: any) => ({
        course_code: x.courseId,
        task_id: x.taskId
      })),
      is_whole_day_overdue: !!isWholeDayOverdue
    };


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

      if (r.ok) res = await r.json().catch(() => ({}));
      else res = null;
    } catch {
      res = null; 
    }

    if (res && res.ok === true) {
      const next = Array.from(new Set([...(recheck.length ? recheck : reported), yest]));
      localStorage.setItem(flagKey, JSON.stringify(next));
    }
  });
}
