# pyright: reportMissingImports=false
import os, json, importlib
from typing import List, Dict, Optional, Any, Tuple
from dotenv import load_dotenv
from .types import TaskWithParts, Part, Preferences
from .scheduler import schedule
from .pdf_ingest import extract_text_from_pdf
from .llm_structures import summarize_task_details



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
    """Divide into equal parts and ensure that each part falls within the range of 30-60 minutes"""
    minutes_total = max(1, int(minutes_total))
    
    #Automatically adjust the number of parts based on the total duration, ensuring that each part falls within the range of 30-60
    if minutes_total < 60:  # The total duration is less than 1 hour, divided into one part of 30-60 minutes
        return [max(30, min(60, minutes_total))]
    
    # Calculate the appropriate number of parts: total duration/45 (median of 30-60)
    optimal_parts = max(2, min(6, round(minutes_total / 45)))
    parts = max(2, min(6, parts if parts <= optimal_parts else optimal_parts))
    
    base = minutes_total // parts
    rem = minutes_total - base * parts
    res = [base] * parts
    for i in range(rem):
        res[-(i + 1)] += 1
    
    # Adjust to ensure that each part is within the range of 30-60
    adjusted = []
    for minutes in res:
        if minutes < 30:
            adjusted.append(30)
        elif minutes > 60:
            # If it exceeds 60, split it into multiple blocks of 30-60
            while minutes > 60:
                adjusted.append(60)
                minutes -= 60
            if minutes >= 30:
                adjusted.append(minutes)
        else:
            adjusted.append(minutes)
    
    return adjusted[:6]  # 6 parts at most

def _heuristic_minutes_from_text(txt: str) -> int:
    words = max(1, len(txt.split()))
    read_minutes = words / 200.0
    impl_minutes = read_minutes * 2.0
    minutes = int(max(180, min(8*60, impl_minutes * 60))) 
    return minutes

def _ai_split_parts(task_title: str, due_date: str, estimated_minutes: int) -> List[Part]:
  
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
    max_retries = 1
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Try to call Gemini API  {attempt + 1}/{max_retries} (plan_generator)")
            

            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10) 
            
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
                    print(f"[DEBUG] no response, retry({attempt + 2}/{max_retries})...")
                    continue
                raise ValueError("Empty model response")

           
            clean_json = raw.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json[7:]  
            if clean_json.endswith('```'):
                clean_json = clean_json[:-3]  
            clean_json = clean_json.strip()
            
            # Fix common JSON formatting issues
            import re
            
            clean_json = re.sub(r'(":\s*"[^"]*")\s*("[\w]+":)', r'\1,\2', clean_json)
         
            clean_json = re.sub(r'(":\s*\d+)\s*("[\w]+":)', r'\1,\2', clean_json)

            clean_json = re.sub(r'}\s*{', r'},{', clean_json)
       
            if clean_json.count('"') % 2 != 0:
                clean_json += '"'
       
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
            
        
            print(f"[DEBUG] ✅ Split into {len(out)} parts")
            return out
            
        except (BrokenPipeError, ConnectionError, OSError) as e:
            print(f"[DEBUG] network err: {type(e).__name__} - {e}")
            print(f"[DEBUG] ❌ API call failed, using intelligent fallback data")
            return _intelligent_fallback_split(task_title, estimated_minutes)
        except Exception as e:
            print(f"[DEBUG] Gemini faile (retry {attempt + 1}/{max_retries}): {type(e).__name__} - {e}")
            print(f"[DEBUG] ❌ fail to decode content, use fall back data")
            return _intelligent_fallback_split(task_title, estimated_minutes)
    
    return _intelligent_fallback_split(task_title, estimated_minutes)

def _parts_from_summary_or_fallback(task_title: str, due_date: str,
                                    est_minutes: int,
                                    summary: Optional[Dict[str, Any]]) -> Tuple[List[Part], str]:
    """
    Prioritize using suggested Parts (including notes) from LLM abstracts, and allocate minutes equally;
Otherwise, use LLM to split; Otherwise, divide equally. Return (parts, explanation)
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
    # No abstract: Attempt to split LLM directly; Otherwise, divide equally
    parts = _ai_split_parts(task_title, due_date, est_minutes)
    return parts, explanation

def _generate_reason_for_part(label: str, index: int, total_parts: int) -> str:
    """Generate reasons for each part in the plan"""
    reasons = [
        "This is foundational and needs to be completed first.",
        "This builds on the previous part and develops core skills.",
        "This applies the concepts from earlier parts.",
        "This reinforces learning and ensures comprehensive understanding.",
        "This finalizes the work and prepares for submission."
    ]
    
    # Generate more specific reasons based on specific keywords on the label
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
        # general reasons
        return reasons[index % len(reasons)]

def _estimate_minutes(est_hours_meta, summary, detail_text: Optional[str]) -> int:
    if est_hours_meta and float(est_hours_meta) > 0:
        return int(round(float(est_hours_meta) * 60))
    if summary and isinstance(summary.get("estimatedHours"), (int, float)) and summary["estimatedHours"] > 0:
        return int(round(float(summary["estimatedHours"]) * 60))
    if detail_text:
        return _heuristic_minutes_from_text(detail_text)
    
    return 6 * 60  

def _to_task_with_parts(meta: Dict[str, Any]) -> Tuple[TaskWithParts, Dict[str, Any]]:
    """
    Return (TaskWithParts, aiTaskInfo)
    aiTaskInfo = {
      "taskId":..., "totalMinutes":..., "explanation": "...",
      "parts":[{"partId","order","title","minutes","notes","percent"}]
    }
    """
    
    # 1) Extract detailed text
    detail_text = meta.get("detailText")
    if not detail_text and meta.get("detailPdfPath"):
        detail_text = extract_text_from_pdf(meta["detailPdfPath"])
    
    # 2) LLM Summary (optional)
    summary = summarize_task_details(meta["task"], meta["dueDate"], detail_text) if detail_text else None

    # 3) Estimated total minutes
    est_minutes = _estimate_minutes(meta.get("estimatedHours"), summary, detail_text)

    # 4) Generate parts+explanation
    parts, explanation = _parts_from_summary_or_fallback(meta["task"], meta["dueDate"], est_minutes, summary)

    # 5) Calculate the percentage and construct aiTaskInfo (including the fields required for Explain My Plan)
    total = sum(max(0, int(p.minutes)) for p in parts) or 1
    ai_parts = []
    for i, p in enumerate(sorted(parts, key=lambda x: x.order)):
        # Generate descriptive labels (remove the prefix 'Part X -')
        label = p.title.replace(f"Part {p.order} - ", "") if f"Part {p.order} - " in p.title else p.title
        
        # Generate detailed instructions
        detail = p.notes or f"Work on {label}"
        
        # Reasons generated in the plan
        why_in_plan = _generate_reason_for_part(label, i, len(parts))
        
        ai_parts.append({
            "partId": p.partId,
            "order": p.order,
            "title": p.title,  
            "label": label,  
            "minutes": int(p.minutes),
            "notes": p.notes or "",
            "detail": detail,   
            "why_in_plan": why_in_plan, 
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

    
    # Pre check: There must be a task with a valid dueDate, otherwise no plan will be generated
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
    
    # Merge AI interpretation information
    result["aiSummary"] = {"tasks": ai_summaries}
    return result

def _intelligent_fallback_split(task_title: str, estimated_minutes: int) -> List[Part]:
    """Intelligent fallback: Generate meaningful section headings based on task types"""
    mins = _equal_split(estimated_minutes, 3)
    
    # Determine the type based on the task title and generate corresponding partial titles
    title_lower = task_title.lower()
    
    if "assignment" in title_lower or "project" in title_lower:
        if "front" in title_lower or "frontend" in title_lower or "ui" in title_lower:
            parts = [
                Part(partId="p1", order=1, title="Part 1 - Setup & Planning", minutes=mins[0], 
                     notes="Set up development environment, analyze requirements"),
                Part(partId="p2", order=2, title="Part 2 - UI Implementation", minutes=mins[1], 
                     notes="Build user interface components and layouts"),
                Part(partId="p3", order=3, title="Part 3 - Testing & Polish", minutes=mins[2], 
                     notes="Test functionality, fix bugs, and polish the interface")
            ]
        else:

            parts = [
                Part(partId="p1", order=1, title="Part 1 - Research & Planning", minutes=mins[0], 
                     notes="Research requirements and plan the approach"),
                Part(partId="p2", order=2, title="Part 2 - Implementation", minutes=mins[1], 
                     notes="Build the main functionality"),
                Part(partId="p3", order=3, title="Part 3 - Review & Finalize", minutes=mins[2], 
                     notes="Review work, test, and finalize submission")
            ]
    else:

        parts = [
            Part(partId="p1", order=1, title="Part 1 - Preparation & Setup", minutes=mins[0], 
                 notes="Prepare materials and understand requirements"),
            Part(partId="p2", order=2, title="Part 2 - Main Work", minutes=mins[1], 
                 notes="Complete the core tasks and objectives"),
            Part(partId="p3", order=3, title="Part 3 - Review & Submission", minutes=mins[2], 
                 notes="Review work and prepare for submission")
        ]
    
    return parts
