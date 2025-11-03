# pyright: reportMissingImports=false
import os, json, importlib
from typing import List, Dict, Optional, Any, Tuple
from dotenv import load_dotenv
from .types import TaskWithParts, Part, Preferences
from .scheduler import schedule
from .pdf_ingest import extract_text_from_pdf
from .llm_structures import summarize_task_details


# 可选：用于“直接让 LLM 拆分成 parts”的兜底模型
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
use_gemini: bool = bool(GEMINI_KEY)
_split_model: Any = None
print("[Gemini Check] GEMINI_KEY found?", bool(GEMINI_KEY)) 

if use_gemini:
    try:
        genai = importlib.import_module("google.generativeai")  # type: ignore[reportMissingImports]
        genai.configure(api_key=GEMINI_KEY)
        _split_model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"temperature": 0.2, "max_output_tokens": 1024}
        )
        print("[Gemini Check] Gemini model loaded successfully ✅")
    except Exception:
        use_gemini = False
        print("[Gemini Check] Failed to load Gemini ❌:")
else:
    print("[Gemini Check] No GEMINI_API_KEY found, using fallback mode ⚙️")


def _equal_split(minutes_total: int, parts: int = 3) -> List[int]:
    """等分拆分，确保每个 part 在 30-60 分钟范围内"""
    minutes_total = max(1, int(minutes_total))
    
    # 根据总时长自动调整 parts 数量，确保每个 part 在 30-60 范围
    if minutes_total < 60:  # 总时长不足1小时，拆成1个30-60分钟的part
        return [max(30, min(60, minutes_total))]
    
    # 计算合适的 parts 数量：总时长 / 45（30-60的中位数）
    optimal_parts = max(2, min(6, round(minutes_total / 45)))
    parts = max(2, min(6, parts if parts <= optimal_parts else optimal_parts))
    
    base = minutes_total // parts
    rem = minutes_total - base * parts
    res = [base] * parts
    for i in range(rem):
        res[-(i + 1)] += 1
    
    # 调整确保每个part在30-60范围内
    adjusted = []
    for minutes in res:
        if minutes < 30:
            adjusted.append(30)
        elif minutes > 60:
            # 如果超过60，拆分成多个30-60的块
            while minutes > 60:
                adjusted.append(60)
                minutes -= 60
            if minutes >= 30:
                adjusted.append(minutes)
        else:
            adjusted.append(minutes)
    
    return adjusted[:6]  # 最多6个part

def _heuristic_minutes_from_text(txt: str) -> int:
    words = max(1, len(txt.split()))
    read_minutes = words / 200.0
    impl_minutes = read_minutes * 2.0
    minutes = int(max(180, min(8*60, impl_minutes * 60)))  # 3h~8h，确保能拆成多个60-90分钟块
    return minutes

def _ai_split_parts(task_title: str, due_date: str, estimated_minutes: int) -> List[Part]:
    """让 LLM 直接拆 2–6 段；失败回退等比分块。"""
    if not use_gemini or _split_model is None:
        mins = _equal_split(estimated_minutes, 3)
        return [Part(partId=f"p{i+1}", order=i+1, title=f"Part {i+1}", minutes=mins[i]) for i in range(len(mins))]
    prompt = f"""
Split the task into 2–6 ordered parts whose minutes sum ≈ {estimated_minutes}.
Each part should be 30-60 minutes (prefer 45 minutes as target).
Return JSON ONLY with array "parts":
{{
  "parts": [
    {{"partId":"p1","order":1,"title":"Part 1","minutes":45,"notes":"what to do"}},
    ...
  ]
}}
No extra text.
Task: "{task_title}"
Due: {due_date}
"""
    try:
        resp = _split_model.generate_content(prompt)
        cands = getattr(resp, "candidates", None) or []
        raw = None
        if cands and getattr(cands[0], "content", None):
            parts = getattr(cands[0].content, "parts", None) or []
            texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
            raw = "\n".join(texts).strip() if texts else None
        if not raw:
            raise ValueError("Empty model response")

        data = json.loads(raw)
        out: List[Part] = []
        for i, p in enumerate(data.get("parts", [])):
            title = str(p.get("title") or f"Part {i+1}")
            out.append(Part(
                partId=str(p.get("partId") or f"p{i+1}"),
                order=int(p.get("order") or (i+1)),
                title=title,
                minutes=int(p.get("minutes") or 0),
                notes=p.get("notes") or f"{title}: focus the next concrete step."
            ))
        if not out or sum(max(0, x.minutes) for x in out) <= 0:
            mins = _equal_split(estimated_minutes, 3)
            out = [Part(partId=f"p{i+1}", order=i+1, title=f"Part {i+1}", minutes=mins[i]) for i in range(len(mins))]
        return out
    except Exception:
        mins = _equal_split(estimated_minutes, 3)
        return [Part(partId=f"p{i+1}", order=i+1, title=f"Part {i+1}", minutes=mins[i]) for i in range(len(mins))]

def _parts_from_summary_or_fallback(task_title: str, due_date: str,
                                    est_minutes: int,
                                    summary: Optional[Dict[str, Any]]) -> Tuple[List[Part], str]:
    """
    优先使用 LLM 摘要的 suggestedParts（含 notes），minutes 用等分分配；
    否则用 LLM 拆分；再否则等分。返回 (parts, explanation)
    """
    print("summary keys:", list(summary.keys()) if summary else None)
    explanation = "Split into ordered parts to progress from setup to implementation to validation."
    if summary and isinstance(summary.get("suggestedParts"), list) and len(summary["suggestedParts"]) >= 2:
        print("[parts] from summary.suggestedParts") 
        parts_raw = summary["suggestedParts"][:6]
        mins = _equal_split(est_minutes, len(parts_raw))
        out: List[Part] = []
        for i, item in enumerate(parts_raw):
            out.append(Part(
                partId=f"p{i+1}",
                order=int(item.get("order") or (i+1)),
                title=str(item.get("title") or f"Part {i+1}"),
                minutes=int(mins[i]),
                notes=item.get("notes") or ""
            ))
        explanation = summary.get("explanation") or explanation
        return out, explanation
    else:
        print("[parts] from ai_split or equal_split") 
    # 没有摘要：尝试 LLM 直接拆分；否则等分
    parts = _ai_split_parts(task_title, due_date, est_minutes)
    return parts, explanation

def _estimate_minutes(est_hours_meta, summary, detail_text: Optional[str]) -> int:
    if est_hours_meta and float(est_hours_meta) > 0:
        return int(round(float(est_hours_meta) * 60))
    if summary and isinstance(summary.get("estimatedHours"), (int, float)) and summary["estimatedHours"] > 0:
        return int(round(float(summary["estimatedHours"]) * 60))
    if detail_text:
        return _heuristic_minutes_from_text(detail_text)
    
    return 6 * 60  # 兜底 6 小时

def _to_task_with_parts(meta: Dict[str, Any]) -> Tuple[TaskWithParts, Dict[str, Any]]:
    """
    返回 (TaskWithParts, aiTaskInfo)
    aiTaskInfo = {
      "taskId":..., "totalMinutes":..., "explanation": "...",
      "parts":[{"partId","order","title","minutes","notes","percent"}]
    }
    """
    
    # 1) 提取详情文本
    detail_text = meta.get("detailText")
    if not detail_text and meta.get("detailPdfPath"):
        detail_text = extract_text_from_pdf(meta["detailPdfPath"])
    
    # 2) LLM 摘要（可选）
    summary = summarize_task_details(meta["task"], meta["dueDate"], detail_text) if detail_text else None

    # 3) 估总分钟
    est_minutes = _estimate_minutes(meta.get("estimatedHours"), summary, detail_text)

    # 4) 生成 parts + explanation
    parts, explanation = _parts_from_summary_or_fallback(meta["task"], meta["dueDate"], est_minutes, summary)

    # 5) 计算百分比，并构造 aiTaskInfo
    total = sum(max(0, int(p.minutes)) for p in parts) or 1
    ai_parts = []
    for p in sorted(parts, key=lambda x: x.order):
        ai_parts.append({
            "partId": p.partId,
            "order": p.order,
            "title": p.title,
            "minutes": int(p.minutes),
            "notes": p.notes or "",
            "percent": round(int(p.minutes) / total * 100, 1)
        })

    ai_info = {
        "taskId": str(meta["id"]),
        "taskTitle": str(meta["task"]),
        "totalMinutes": int(total),
        "explanation": explanation,
        "parts": ai_parts
    }
    print("[debug] meta keys:", list(meta.keys()))
    print("[debug] detailText len:", len(meta.get("detailText","")) if meta.get("detailText") else None)
    print("[debug] detailPdfPath:", meta.get("detailPdfPath"))
    print("[debug] summary type:", type(summary))

    return TaskWithParts(
        taskId=str(meta["id"]),
        taskTitle=str(meta["task"]),
        dueDate=str(meta["dueDate"]),
        parts=parts
    ), ai_info

def generate_plan(preferences: Dict[str, Any], tasks_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
    preferences = {
    "daily_hour_cap": preferences.get("dailyHours"),
    "weekly_study_days": preferences.get("weeklyStudyDays"),
    "avoid_days": preferences.get("avoidDays"),
}
    
    # 预检：必须存在带合法 dueDate 的任务，否则不生成计划
    from datetime import datetime
    valid_tasks = []
    for m in tasks_meta or []:
        try:
            if m.get("dueDate"):
                _ = datetime.fromisoformat(str(m["dueDate"]))
                valid_tasks.append(m)
        except Exception:
            continue
    if not valid_tasks:
        return {"ok": False, "message": "No course tasks found — cannot generate a plan."}

    task_objs: List[TaskWithParts] = []
    ai_summaries: List[Dict[str, Any]] = []
    for m in valid_tasks:
        t, info = _to_task_with_parts(m)
        task_objs.append(t)
        ai_summaries.append(info)
    prefs = Preferences(
        daily_hour_cap=int(preferences.get("daily_hour_cap", 3)),
        weekly_study_days=int(preferences.get("weekly_study_days", 5)),
        avoid_days=preferences.get("avoid_days") or []
    )

    result = schedule(task_objs, prefs)
    
    # 合并 AI 解释信息
    result["aiSummary"] = {"tasks": ai_summaries}
    return result