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
        return [Part(partId=f"p{i+1}", order=i+1, title=f"Part {i+1} - General Task", minutes=mins[i]) for i in range(len(mins))]
    prompt = f"""
Split the task into 2–6 ordered parts whose minutes sum ≈ {estimated_minutes}.
Each part should be 30-60 minutes (prefer 45 minutes as target).
Return ONLY valid JSON in this exact format:
{{"parts":[{{"partId":"p1","order":1,"title":"Setup & Planning","minutes":45,"notes":"what to do"}},{{"partId":"p2","order":2,"title":"Implementation","minutes":45,"notes":"what to do"}}]}}

IMPORTANT: 
- The "title" field should be a descriptive name (like "Setup & Planning", "Implementation", "Testing"), NOT "Part 1", "Part 2"
- Return ONLY the JSON, no markdown, no extra text
- Ensure all commas and quotes are correct

Task: "{task_title}"
Due: {due_date}
"""
    # 🔥 添加重试机制，处理网络连接问题
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Gemini API 调用尝试 {attempt + 1}/{max_retries} (plan_generator)")
            
            # 设置超时时间
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(30)  # 30秒超时
            
            try:
                resp = _split_model.generate_content(prompt)
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            cands = getattr(resp, "candidates", None) or []
            raw = None
            if cands and getattr(cands[0], "content", None):
                parts = getattr(cands[0].content, "parts", None) or []
                texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
                raw = "\n".join(texts).strip() if texts else None
            if not raw:
                if attempt < max_retries - 1:
                    print(f"[DEBUG] 模型返回为空，重试 ({attempt + 2}/{max_retries})...")
                    continue
                raise ValueError("Empty model response")

            # 清理 Gemini 返回的 markdown 格式
            clean_json = raw.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json[7:]  # 移除 ```json
            if clean_json.endswith('```'):
                clean_json = clean_json[:-3]  # 移除 ```
            clean_json = clean_json.strip()
            
            # 修复常见的 JSON 格式问题
            import re
            # 在 "key":"value" 后面添加逗号（如果后面跟着 "key"）
            clean_json = re.sub(r'(":\s*"[^"]*")\s*("[\w]+":)', r'\1,\2', clean_json)
            # 在 "key":number 后面添加逗号（如果后面跟着 "key"）
            clean_json = re.sub(r'(":\s*\d+)\s*("[\w]+":)', r'\1,\2', clean_json)
            # 在对象结束 } 前面添加逗号（如果后面跟着 {）
            clean_json = re.sub(r'}\s*{', r'},{', clean_json)
            # 修复未终止的字符串：如果字符串没有结束引号，尝试添加
            if clean_json.count('"') % 2 != 0:
                clean_json += '"'
            # 确保 JSON 对象正确关闭
            open_braces = clean_json.count('{') - clean_json.count('}')
            clean_json += '}' * open_braces
            open_brackets = clean_json.count('[') - clean_json.count(']')
            clean_json += ']' * open_brackets
            
            data = json.loads(clean_json)
            out: List[Part] = []
            for i, p in enumerate(data.get("parts", [])):
                base_title = str(p.get("title") or f"General Task")
                order = int(p.get("order") or (i+1))
                formatted_title = f"Part {order} - {base_title}"
                out.append(Part(
                    partId=str(p.get("partId") or f"p{i+1}"),
                    order=order,
                    title=formatted_title,
                    minutes=int(p.get("minutes") or 0),
                    notes=p.get("notes") or f"{formatted_title}: focus the next concrete step."
                ))
            if not out or sum(max(0, x.minutes) for x in out) <= 0:
                mins = _equal_split(estimated_minutes, 3)
                out = [Part(partId=f"p{i+1}", order=i+1, title=f"Part {i+1} - General Task", minutes=mins[i]) for i in range(len(mins))]
            
            # 成功解析，返回结果
            print(f"[DEBUG] ✅ 成功拆分为 {len(out)} 个parts")
            return out
            
        except (BrokenPipeError, ConnectionError, OSError) as e:
            print(f"[DEBUG] 网络连接错误 (尝试 {attempt + 1}/{max_retries}): {type(e).__name__} - {e}")
            if attempt < max_retries - 1:
                import time
                wait_time = (attempt + 1) * 2  # 递增等待时间: 2s, 4s, 6s
                print(f"[DEBUG] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[DEBUG] ❌ 达到最大重试次数，使用fallback")
                return _intelligent_fallback_split(task_title, estimated_minutes)
        except Exception as e:
            print(f"[DEBUG] Gemini 调用异常 (尝试 {attempt + 1}/{max_retries}): {type(e).__name__} - {e}")
            if attempt < max_retries - 1:
                import time
                print(f"[DEBUG] 等待 2 秒后重试...")
                time.sleep(2)
                continue
            # 最后一次尝试失败，使用 fallback
            return _intelligent_fallback_split(task_title, estimated_minutes)
    
    # 不应该到达这里，但以防万一
    return _intelligent_fallback_split(task_title, estimated_minutes)

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
            base_title = str(item.get("title") or "General Task")
            order = int(item.get("order") or (i+1))
            formatted_title = f"Part {order} - {base_title}"
            out.append(Part(
                partId=f"p{i+1}",
                order=order,
                title=formatted_title,
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

def _generate_reason_for_part(label: str, index: int, total_parts: int) -> str:
    """为每个part生成在计划中的原因"""
    reasons = [
        "This is foundational and needs to be completed first.",
        "This builds on the previous part and develops core skills.",
        "This applies the concepts from earlier parts.",
        "This reinforces learning and ensures comprehensive understanding.",
        "This finalizes the work and prepares for submission."
    ]
    
    # 根据label的特定关键词生成更具体的原因
    label_lower = label.lower()
    
    if any(word in label_lower for word in ["setup", "research", "planning", "analysis"]):
        return "This is the foundation phase and must be completed before implementation."
    elif any(word in label_lower for word in ["implementation", "coding", "development", "design"]):
        return "This is the main implementation work that applies your planning and research."
    elif any(word in label_lower for word in ["test", "testing", "validation", "review"]):
        return "Testing ensures your implementation works correctly and meets requirements."
    elif any(word in label_lower for word in ["documentation", "report", "write", "final"]):
        return "This finalizes your work and communicates your solution clearly."
    elif any(word in label_lower for word in ["data", "database", "schema", "model"]):
        return "This establishes the data structure needed for the rest of the project."
    elif any(word in label_lower for word in ["ui", "interface", "frontend", "user"]):
        return "This creates the user-facing components of your application."
    elif any(word in label_lower for word in ["backend", "server", "api", "logic"]):
        return "This implements the core business logic and functionality."
    else:
        # 使用通用原因
        return reasons[index % len(reasons)]

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

    # 5) 计算百分比，并构造 aiTaskInfo（包含Explain My Plan需要的字段）
    total = sum(max(0, int(p.minutes)) for p in parts) or 1
    ai_parts = []
    for i, p in enumerate(sorted(parts, key=lambda x: x.order)):
        # 生成描述性标签（移除"Part X - "前缀）
        label = p.title.replace(f"Part {p.order} - ", "") if f"Part {p.order} - " in p.title else p.title
        
        # 生成详细说明
        detail = p.notes or f"Work on {label}"
        
        # 生成在计划中的原因
        why_in_plan = _generate_reason_for_part(label, i, len(parts))
        
        ai_parts.append({
            "partId": p.partId,
            "order": p.order,
            "title": p.title,  # 保留原始标题
            "label": label,   # 新增：描述性标签
            "minutes": int(p.minutes),
            "notes": p.notes or "",
            "detail": detail,    # 新增：详细说明
            "why_in_plan": why_in_plan,  # 新增：在计划中的原因
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

def generate_plan(preferences: Dict[str, Any], tasks_meta: List[Dict[str, Any]], user_timezone: str = 'UTC') -> Dict[str, Any]:
    # 参数已经从 views.py 正确传入，不需要重新映射
    
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
        daily_hour_cap=int(preferences.get("daily_hour_cap", 3) or 3),
        weekly_study_days=int(preferences.get("weekly_study_days", 5) or 5),
        avoid_days=preferences.get("avoid_days") or []
    )

    result = schedule(task_objs, prefs, user_timezone=user_timezone)
    
    # 合并 AI 解释信息
    result["aiSummary"] = {"tasks": ai_summaries}
    return result

def _intelligent_fallback_split(task_title: str, estimated_minutes: int) -> List[Part]:
    """智能fallback：根据任务类型生成有意义的部分标题"""
    mins = _equal_split(estimated_minutes, 3)
    
    # 根据任务标题判断类型并生成相应的部分标题
    title_lower = task_title.lower()
    
    if "assignment" in title_lower or "project" in title_lower:
        if "front" in title_lower or "frontend" in title_lower or "ui" in title_lower:
            # 前端项目
            parts = [
                Part(partId="p1", order=1, title="Part 1 - Setup & Planning", minutes=mins[0], 
                     notes="Set up development environment, analyze requirements"),
                Part(partId="p2", order=2, title="Part 2 - UI Implementation", minutes=mins[1], 
                     notes="Build user interface components and layouts"),
                Part(partId="p3", order=3, title="Part 3 - Testing & Polish", minutes=mins[2], 
                     notes="Test functionality, fix bugs, and polish the interface")
            ]
        else:
            # 通用项目
            parts = [
                Part(partId="p1", order=1, title="Part 1 - Research & Planning", minutes=mins[0], 
                     notes="Research requirements and plan the approach"),
                Part(partId="p2", order=2, title="Part 2 - Implementation", minutes=mins[1], 
                     notes="Build the main functionality"),
                Part(partId="p3", order=3, title="Part 3 - Review & Finalize", minutes=mins[2], 
                     notes="Review work, test, and finalize submission")
            ]
    else:
        # 默认通用结构
        parts = [
            Part(partId="p1", order=1, title="Part 1 - Preparation & Setup", minutes=mins[0], 
                 notes="Prepare materials and understand requirements"),
            Part(partId="p2", order=2, title="Part 2 - Main Work", minutes=mins[1], 
                 notes="Complete the core tasks and objectives"),
            Part(partId="p3", order=3, title="Part 3 - Review & Submission", minutes=mins[2], 
                 notes="Review work and prepare for submission")
        ]
    
    return parts
