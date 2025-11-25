import os, json, importlib
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

use_gemini: bool = bool(GEMINI_KEY)
genai: Any = None  
_model: Any = None  

if use_gemini:
    try:
        genai = importlib.import_module("google.generativeai")  # type: ignore[reportMissingImports]
        genai.configure(api_key=GEMINI_KEY )
        _model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"temperature": 0.2, "max_output_tokens": 2048}
        )
       
    except Exception as e:
        print(f"[DEBUG] Gemini model fail to initialize: {e}")
        use_gemini = False

def summarize_task_details(task_title: str, due_date: str, raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Let LLM extract estimated dates, suggested parts (including notes), and explanations from PDF text.
    Failed to return None   
    """
    if not use_gemini or not _model or not raw_text or len(raw_text) < 50:
        print(f"[DEBUG] Skip Gemini analysis: use_gemini={use_gemini}, _model={_model}, text_len={len(raw_text) if raw_text else 0}")
        return None
    # Limit input length to avoid exceeding token limit
    text_limit = min(6000, len(raw_text))
    limited_text = raw_text[:text_limit]
    
    prompt = f"""
Analyze this assignment and return JSON only:
{{
  "estimatedHours": 4,
  "suggestedParts": [
    {{"order": 1, "title": "Setup & Research", "notes": "Read requirements"}},
    {{"order": 2, "title": "Implementation", "notes": "Core coding work"}}
  ],
  "explanation": "Brief explanation of the split strategy"
}}

Task: {task_title}
Due: {due_date}
Content: {limited_text}

JSON only, no markdown:"""
    max_retries = 1
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] try to use Gemini API  {attempt + 1}/{max_retries}")

            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)  
            
            try:
                resp = _model.generate_content(prompt)
                print(f"[DEBUG] Gemini response: {resp}")
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            cands = getattr(resp, "candidates", None) or []
            print(f"[DEBUG] Number of candidates: {len(cands)}")
            if not cands or not getattr(cands[0], "content", None):
                print("[DEBUG] No valid candidates or content")
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Retrying ({attempt + 2}/{max_retries})...")
                    continue
                return None

            parts = getattr(cands[0].content, "parts", None) or []
            texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
            raw = "\n".join(texts).strip()
            print(f"[DEBUG] Extracted text: {raw[:500]}...")

            if not raw:
                print("[DEBUG] Extracted text is empty")
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Retrying ({attempt + 2}/{max_retries})...")
                    continue
                return None
                
            
            clean_json = raw.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json[7:]
            if clean_json.startswith('```'):
                clean_json = clean_json[3:]
            if clean_json.endswith('```'):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()
            
            print(f"[DEBUG] Cleaned JSON: {clean_json}")
            data = json.loads(clean_json)
            print(f"[DEBUG] Parsed JSON: {data}")

            if "suggestedParts" not in data or not isinstance(data["suggestedParts"], list):
                print("[DEBUG] JSON format does not match expectations, returning None")
                return None

            print(f"[DEBUG] ✅ Successfully parsed Gemini response")
            return data
            
        except (BrokenPipeError, ConnectionError, OSError) as e:
            print(f"[DEBUG] Network connection error: {type(e).__name__} - {e}")
            print(f"[DEBUG] ❌ API call failed, returning None")
            import traceback
            traceback.print_exc()
            return None

        except Exception as e:
            print(f"[DEBUG] Gemini exception: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            print(f"[DEBUG] ❌ Call failed, returning None")
            return None
    
    return None