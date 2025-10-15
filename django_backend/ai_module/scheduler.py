from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Tuple, Any
from .types import TaskWithParts, Preferences

def iso_to_date(s: str) -> date:
    return datetime.fromisoformat(s).date()

def week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())  # 周一

def compute_part_percentages(task: TaskWithParts) -> List[Dict[str, Any]]:
    total = sum(max(0, int(p.minutes)) for p in task.parts) or 1
    out = []
    for p in task.parts:
        out.append({
            "partId": p.partId,
            "order": p.order,
            "minutes": int(p.minutes),
            "percent": round(int(p.minutes) / total * 100, 1)
        })
    return out

def _allowed_weekdays_for_week(weekly_study_days: int, avoid_days: set[int]) -> List[int]:
    """
    返回一周中允许学习的 weekday 列表（0..6），
    规则：先去掉 avoid_days，再从小到大取前 N 个（N=weekly_study_days）。
    """
    base = [i for i in range(7) if i not in avoid_days]
    if weekly_study_days >= len(base):
        return base
    return base[:max(0, weekly_study_days)]

def schedule(tasks: List[TaskWithParts], prefs: Preferences, today: Optional[date] = None) -> Dict[str, Any]:
    """
    把按顺序的 parts 放入实际日期 blocks。
    规则：
    - 严格保序（P1→P2→…）
    - 不超过各任务 dueDate
    - ≤ daily_hour_cap 小时/日；放松时可至 10h/日
    - 每周仅允许 weekly_study_days 天；可逐步放宽（先扩大天数，再允许 avoid days，再升日上限）
    - 根据任务量智能计算开始时间，不要过早开始
    - 周视图：从计算出的开始周到最晚 dueDate 所在周周日
    放松阶梯（不足时）：
      1) expand-days-per-week：在不使用 avoid days 前提下，扩大 weekly_study_days 到可用工作日上限
      2) allow-avoid-days：允许使用 avoid days
      3) max10h：把每日上限提升到 10h
    仍不足：返回 impossible，并列出无法安放的 parts。
    """
    today = today or date.today()

    if not tasks:
        return {"ok": False, "message": "No course tasks found — cannot generate a plan.", "weekStart": week_monday(today).isoformat()}

    latest_due = max(iso_to_date(t.dueDate) for t in tasks)
    
    # 计算智能开始时间
    def calculate_smart_start_date() -> date:
        # 计算总工作量（分钟）
        total_minutes = sum(int(max(0, p.minutes)) for t in tasks for p in t.parts)
        
        # 基于偏好计算每周可用分钟数
        daily_cap_min = int(prefs.daily_hour_cap) * 60
        weekly_days = max(1, min(7, int(prefs.weekly_study_days)))
        weekly_capacity = daily_cap_min * weekly_days
        
        # 计算需要的周数（向上取整）
        import math
        weeks_needed = math.ceil(total_minutes / weekly_capacity) if weekly_capacity > 0 else 1
        
        # 从最早截止日期往前推算，加上1周缓冲
        earliest_due = min(iso_to_date(t.dueDate) for t in tasks)
        buffer_weeks = 1  # 1周缓冲时间
        calculated_start = earliest_due - timedelta(weeks=weeks_needed + buffer_weeks)
        
        # 不能早于今天
        smart_start = max(today, calculated_start)
        
        print(f"📊 智能开始时间计算:")
        print(f"   总工作量: {total_minutes}分钟 ({total_minutes/60:.1f}小时)")
        print(f"   每周容量: {weekly_capacity}分钟 ({weekly_capacity/60:.1f}小时)")
        print(f"   需要周数: {weeks_needed}周")
        print(f"   最早截止: {earliest_due}")
        print(f"   计算开始: {calculated_start}")
        print(f"   实际开始: {smart_start}")
        
        return smart_start
    
    smart_start = calculate_smart_start_date()
    start = week_monday(smart_start)
    end = week_monday(latest_due) + timedelta(days=6)
    
    print(f"📅 调度时间范围: {start} 到 {end}")

    def build_days(daily_cap_min: int, weekly_days: int, avoid_set: set[int]) -> List[Dict[str, Any]]:
        days: List[Dict[str, Any]] = []
        d = start
        allowed_weekdays = set(_allowed_weekdays_for_week(weekly_days, avoid_set))
        while d <= end:
            # 严格检查：只有在allowed_weekdays中的日期才有capacity
            cap = daily_cap_min if d.weekday() in allowed_weekdays else 0
            days.append({"date": d.isoformat(), "capacity": cap, "used": 0, "blocks": []})
            d += timedelta(days=1)
        return days

    def try_place(
        daily_cap_min: int,
        weekly_days: int,
        avoid_set: set[int]
    ) -> Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        # 返回 (ok, days, summary, unplacedParts)
        days = build_days(daily_cap_min, weekly_days, avoid_set)
        tasks_sorted = sorted(tasks, key=lambda t: iso_to_date(t.dueDate))
        unplaced: List[Dict[str, Any]] = []

        for t in tasks_sorted:
            due = iso_to_date(t.dueDate)
            for p in sorted(t.parts, key=lambda x: x.order):
                remain = int(max(0, p.minutes))
                # 分散排布：计算可用天数，均匀分配
                available_days = [day for day in days 
                                if datetime.fromisoformat(day["date"]).date() <= due 
                                and day["capacity"] > 0]
                
                if not available_days:
                    # 没有可用天数，直接标记为未安排
                    continue
                
                # 每个part作为整体（60-90分钟）分散到不同天
                part_minutes = int(p.minutes)
                if part_minutes <= 0:
                    continue
                
                # 寻找最佳的一天来放置这个完整的part
                best_day = None
                for day in available_days:
                    free = day["capacity"] - day["used"]
                    if free >= part_minutes:
                        best_day = day
                        break
                
                if best_day:
                    # 找到合适的天，放置整个part
                    best_day["blocks"].append({
                        "taskId": t.taskId,
                        "partId": p.partId,
                        "title": p.title,
                        "minutes": part_minutes,
                        "reason": "within-preference" if daily_cap_min < (10*60) else "max10h"
                    })
                    best_day["used"] += part_minutes
                    remain = 0  # 整个part已安排完毕
                else:
                    # 没找到能容纳整个part的天，尝试拆分为30-60分钟块分散安排
                    while remain >= 30 and available_days:
                        # 优先使用60分钟块，如果剩余不足60或会产生<30尾巴则用30
                        chunk = 60 if (remain >= 60 and (remain - 60 == 0 or remain - 60 >= 30)) else 30
                        
                        # 寻找能容纳这个chunk的天
                        target_day = None
                        for day in available_days:
                            free = day["capacity"] - day["used"]
                            if free >= chunk:
                                target_day = day
                                break
                        
                        if target_day:
                            title = p.title if chunk == int(p.minutes) else f"{p.title} (cont.)"
                            target_day["blocks"].append({
                                "taskId": t.taskId,
                                "partId": p.partId,
                                "title": title,
                                "minutes": chunk,
                                "reason": "within-preference" if daily_cap_min < (10*60) else "max10h"
                            })
                            target_day["used"] += chunk
                            remain -= chunk
                            
                            # 如果这天用完了，从可用天列表中移除
                            if target_day["capacity"] - target_day["used"] < 30:
                                available_days.remove(target_day)
                        else:
                            # 没有天能容纳，跳出循环
                            break

                if remain > 0:
                    unplaced.append({
                        "taskId": t.taskId,
                        "partId": p.partId,
                        "title": p.title,
                        "minutes_remaining": int(remain),
                        "dueDate": t.dueDate
                    })

        summary: List[Dict[str, Any]] = []  # 延后统一生成（避免重复），下方生成一次

        # 统一生成 summary（和原实现一致，便于前端渲染）
        tasks_sorted = sorted(tasks, key=lambda t: iso_to_date(t.dueDate))
        summary = [{
            "taskId": t.taskId,
            "taskTitle": t.taskTitle,
            "totalMinutes": sum(int(px.minutes) for px in t.parts),
            "parts": compute_part_percentages(t)
        } for t in tasks_sorted]

        ok = len(unplaced) == 0
        out_days = [{"date": day["date"], "blocks": day["blocks"]} for day in days]
        return ok, out_days, summary, unplaced

    # 快速总量可行性估算（粗粒度）：统计规划区间内可用总分钟 vs 需求总分钟
    base_daily = int(prefs.daily_hour_cap) * 60
    base_weekly_days = max(1, min(7, int(prefs.weekly_study_days)))
    base_avoid = set(prefs.avoid_days or [])

    total_need = sum(int(max(0, p.minutes)) for t in tasks for p in t.parts)
    # 可用日列表（不考虑 due，仅到全局最晚 due 周日），更严格的 due 约束交给 try_place
    base_days = build_days(base_daily, base_weekly_days, base_avoid)
    total_avail = sum((d["capacity"]) for d in base_days)

    # 阶梯 0：原偏好
    ok0, days0, summary0, unplaced0 = try_place(base_daily, base_weekly_days, base_avoid)
    if ok0:
        return {"ok": True, "relaxation": "none", "weekStart": start.isoformat(), "days": days0, "taskSummary": summary0}

    # 阶梯 1：扩大学习天数（不动 avoid）
    non_avoid = set(i for i in range(7) if i not in base_avoid)
    step1_weekly = min(7, max(base_weekly_days, len(non_avoid)))
    ok1, days1, summary1, unplaced1 = try_place(base_daily, step1_weekly, base_avoid)
    if ok1:
        return {"ok": True, "relaxation": "expand-days-per-week", "weekStart": start.isoformat(), "days": days1, "taskSummary": summary1}

    # 阶梯 2：允许使用 avoid days
    ok2, days2, summary2, unplaced2 = try_place(base_daily, 7, set())
    if ok2:
        return {"ok": True, "relaxation": "allow-avoid-days", "weekStart": start.isoformat(), "days": days2, "taskSummary": summary2}

    # 阶梯 3：把每日上限提升到 10h/日（在允许 avoid days 的基础上）
    ok3, days3, summary3, unplaced3 = try_place(10*60, 7, set())
    if ok3:
        return {"ok": True, "relaxation": "max10h", "weekStart": start.isoformat(), "days": days3, "taskSummary": summary3}

    # 仍不足
    return {
        "ok": False,
        "relaxation": "impossible",
        "message": "Insufficient time — cannot generate plan.",
        "unplaceableParts": unplaced3,
        "weekStart": start.isoformat()
    }