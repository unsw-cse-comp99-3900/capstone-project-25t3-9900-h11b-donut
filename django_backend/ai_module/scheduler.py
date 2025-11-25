from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Tuple, Any
from .types import TaskWithParts, Preferences
def _normalize_avoid_days(raw) -> set[int]:
    """支持字符串和整数混合输入"""
    name2idx = {"Mon":0, "Tue":1, "Wed":2, "Thu":3, "Fri":4, "Sat":5, "Sun":6}
    out: set[int] = set()
    for x in (raw or []):
        if isinstance(x, int):
            out.add(x % 7)
        elif isinstance(x, str):
            xs = x.strip()
            if xs in name2idx:
                out.add(name2idx[xs])
            elif xs.isdigit():
                out.add(int(xs) % 7)
    return out
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

def _allowed_weekdays_for_week(weekly_study_days: int, avoid_days: set[int],start_weekday: int) -> List[int]:
    """
    Return the list of allowed study days for a week (0.. 6),
Rule: First remove avoid_days. If today is a day to avoid, start from tomorrow
    """
    allowed = [i for i in range(7) if i not in avoid_days]
    
    # If today is the day to avoid, start tomorrow
    if start_weekday in avoid_days:
        start_weekday = (start_weekday + 1) % 7
    
    order = [(start_weekday + k) % 7 for k in range(7)]  # Rolling order of the week
    picked = [d for d in order if d in allowed][:min(weekly_study_days, len(allowed))]
    return picked
    # base = [i for i in range(7) if i not in avoid_days]
    # if weekly_study_days >= len(base):
    #     return base
    # return base[:max(0, weekly_study_days)]

def schedule(tasks: List[TaskWithParts], prefs: Preferences, today: Optional[date] = None, user_timezone: str = 'UTC') -> Dict[str, Any]:
    """
    Put the parts in order into the actual date blocks.
    Rule:
    -Strictly maintain order (P1 → P2 →...)
    -Not exceeding the dueDate of each task
    -≤ daily hours/day; Relaxation can last up to 10 hours per day
    -Only weekly_sttudy_days are allowed per week; Can be gradually relaxed (first expanding the number of days, then allowing avoid days, and then raising the daily limit)
    -Intelligent calculation of start time based on task volume, do not start too early
    -Weekly view: From the calculated start to the latest due date on the Sunday of the week
    Relaxation ladder (when insufficient):
    1) Expand days per week: Expand weekly_sttudy_days to the upper limit of available working days without using avoid days
    2) Allow avoidance days: Allow the use of avoid days
    3) Max10h: Increase the daily limit to 10h
    Still insufficient: Return 'impossible' and list the parts that cannot be placed.
    """

    print("===  prefs ===")
    print("daily_hour_cap:", prefs.daily_hour_cap)
    print("weekly_study_days:", prefs.weekly_study_days)
    print("avoid_days origin value:", prefs.avoid_days)
    print("type:", type(prefs.avoid_days))

    if prefs.avoid_days:
        for i, v in enumerate(prefs.avoid_days):
            print(f"  [{i}] {v!r} ({type(v)})")


    # timezone adjustment
    if today is None:
        import pytz
        from django.utils import timezone as django_timezone
        try:
            user_tz = pytz.timezone(user_timezone)
            today_local = django_timezone.now().astimezone(user_tz).date()
        except Exception:
            # invalid tz->utc
            today_local = date.today()
        today = today_local

    if not tasks:
        return {"ok": False, "message": "No course tasks found — cannot generate a plan.", "weekStart": week_monday(today).isoformat()}

    latest_due = max(iso_to_date(t.dueDate) for t in tasks)
    
    # Calculate the start time of intelligent computing
    def calculate_smart_start_date() -> date:
        # total study time
        total_minutes = sum(int(max(0, p.minutes)) for t in tasks for p in t.parts)
        
        # Calculate weekly available minutes based on preferences
        daily_cap_min = int(prefs.daily_hour_cap) * 60
        weekly_days = max(1, min(7, int(prefs.weekly_study_days)))
        weekly_capacity = daily_cap_min * weekly_days
        
        # Calculate the required number of weeks (rounded up)
        import math
        weeks_needed = math.ceil(total_minutes / weekly_capacity) if weekly_capacity > 0 else 1
        
        # Starting from the earliest deadline and adding a one week buffer
        earliest_due = min(iso_to_date(t.dueDate) for t in tasks)
        buffer_weeks = 1  # 1week buffer time
        calculated_start = earliest_due - timedelta(weeks=weeks_needed + buffer_weeks)
        
        # no earlier than today
        smart_start = max(today, calculated_start)
  
        
        return smart_start
    
    smart_start = calculate_smart_start_date()
    #start = week_monday(smart_start)
    start = today # start from now
    end = week_monday(latest_due) + timedelta(days=6)
    
  

    def build_days(daily_cap_min: int, weekly_days: int, avoid_set: set[int]) -> List[Dict[str, Any]]:

        days: List[Dict[str, Any]] = []
        #If the start date is the number of days to avoid, start from the next day
        d = start
        if d.weekday() in avoid_set:
            d = d + timedelta(days=1)
        
        while d <= end:
            week_start = week_monday(d)
            is_first_week = (week_start == week_monday(start))
            start_wd = start.weekday() if is_first_week else 0

            allowed_weekdays = set(_allowed_weekdays_for_week(weekly_days, avoid_set, start_wd))

            for offset in range(7):
                cur = week_start + timedelta(days=offset)
                if cur > end:
                    break
                cap = daily_cap_min if (cur.weekday() in allowed_weekdays and cur >= today) else 0
                if cur >= d:
                    days.append({"date": cur.isoformat(), "capacity": cap, "used": 0, "blocks": []})
            d = week_start + timedelta(days=7)
        return days
    
    def try_place(
        daily_cap_min: int,
        weekly_days: int,
        avoid_set: set[int]
    ) -> Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        # return (ok, days, summary, unplacedParts)
        days = build_days(daily_cap_min, weekly_days, avoid_set)
        tasks_sorted = sorted(tasks, key=lambda t: iso_to_date(t.dueDate))
        unplaced: List[Dict[str, Any]] = []

        for t in tasks_sorted:
            due = iso_to_date(t.dueDate)
            for p in sorted(t.parts, key=lambda x: x.order):
                remain = int(max(0, p.minutes))
                # Distributed arrangement: Calculate the number of available days and evenly distribute them
                available_days = [
                                    day for day in days
                                    if (today <= datetime.fromisoformat(day["date"]).date() <= due)
                                    and day["capacity"] > 0
                                ]
                if not available_days:
                    # There are no available days, just mark as not scheduled
                    continue
                
              #Each part as a whole (60-90 minutes) is dispersed to different days
                part_minutes = int(p.minutes)
                if part_minutes <= 0:
                    continue
                
                # Find the best day to place this complete part
                best_day = None
                for day in available_days:
                    free = day["capacity"] - day["used"]
                    if free >= part_minutes:
                        best_day = day
                        break
                
                if best_day:
                    # Find a suitable day and place the entire part
                    best_day["blocks"].append({
                        "taskId": t.taskId,
                        "partId": p.partId,
                        "title": p.title,
                        "minutes": part_minutes,
                        "reason": "within-preference" if daily_cap_min < (10*60) else "max10h"
                    })
                    best_day["used"] += part_minutes
                    remain = 0 
                else:
                    #Unable to find a day that can accommodate the entire part, try splitting it into 30-60 minute blocks and arranging them separately
                    while remain >= 30 and available_days:
                       
                        chunk = 60 if (remain >= 60 and (remain - 60 == 0 or remain - 60 >= 30)) else 30
                        
                        #Find a day that can accommodate this chunk
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
                            
                            # If the day is used up, remove it from the list of available days
                            if target_day["capacity"] - target_day["used"] < 30:
                                available_days.remove(target_day)
                        else:
                            # No days can accommodate it, break out of the cycle
                            break

                if remain > 0:
                    unplaced.append({
                        "taskId": t.taskId,
                        "partId": p.partId,
                        "title": p.title,
                        "minutes_remaining": int(remain),
                        "dueDate": t.dueDate
                    })

        summary: List[Dict[str, Any]] = []  #Delay unified generation (to avoid duplication), generate once below

        # Unified generation of summary (consistent with the original implementation for easy front-end rendering)
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

    # Rapid Total Feasibility Estimation (Coarse grained): Total minutes available within the statistical planning interval vs. total minutes required
    base_daily = int(prefs.daily_hour_cap) * 60
    base_weekly_days = max(1, min(7, int(prefs.weekly_study_days)))
    #base_avoid = set(prefs.avoid_days or [])
    base_avoid = _normalize_avoid_days(prefs.avoid_days)
    
    total_need = sum(int(max(0, p.minutes)) for t in tasks for p in t.parts)
    #List of available days (excluding due, only up to the latest due Sunday globally), with stricter due constraints assigned to try_place
    base_days = build_days(base_daily, base_weekly_days, base_avoid)
    total_avail = sum((d["capacity"]) for d in base_days)


    ok0, days0, summary0, unplaced0 = try_place(base_daily, base_weekly_days, base_avoid)
    if ok0:
        return {"ok": True, "relaxation": "none", "weekStart": start.isoformat(), "days": days0, "taskSummary": summary0}


    non_avoid = set(i for i in range(7) if i not in base_avoid)
    step1_weekly = min(7, max(base_weekly_days, len(non_avoid)))
    ok1, days1, summary1, unplaced1 = try_place(base_daily, step1_weekly, base_avoid)
    if ok1:
        return {"ok": True, "relaxation": "expand-days-per-week", "weekStart": start.isoformat(), "days": days1, "taskSummary": summary1}


    ok2, days2, summary2, unplaced2 = try_place(base_daily, 7, set())
    if ok2:
        return {"ok": True, "relaxation": "allow-avoid-days", "weekStart": start.isoformat(), "days": days2, "taskSummary": summary2}


    ok3, days3, summary3, unplaced3 = try_place(10*60, 7, set())
    if ok3:
        return {"ok": True, "relaxation": "max10h", "weekStart": start.isoformat(), "days": days3, "taskSummary": summary3}


    return {
        "ok": False,
        "relaxation": "impossible",
        "message": "Insufficient time — cannot generate plan.",
        "unplaceableParts": unplaced3,
        "weekStart": start.isoformat()
    }