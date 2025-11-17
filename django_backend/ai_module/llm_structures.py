import os, json, importlib
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# 确保加载正确的.env文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

use_gemini: bool = bool(GEMINI_KEY)
genai: Any = None  # 动态导入以避免类型检查报错
_model: Any = None  # 初始化模型变量


if use_gemini:
    try:
        genai = importlib.import_module("google.generativeai")  # type: ignore[reportMissingImports]
        genai.configure(
                api_key=GEMINI_KEY,
                transport="rest",  
            )
        _model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"temperature": 0.2, "max_output_tokens": 2048}
        )
        # print(f"[DEBUG] Gemini模型初始化成功: {_model}")
    except Exception as e:
        print(f"[DEBUG] Gemini模型初始化失败: {e}")
        use_gemini = False

def summarize_task_details(task_title: str, due_date: str, raw_text: str) -> Optional[Dict[str, Any]]:
    """
    让 LLM 从 PDF 文本中提取：estimatedHours、suggestedParts（含 notes）、explanation。
    失败返回 None（调用方兜底）。
    """
    if not use_gemini or not _model or not raw_text or len(raw_text) < 50:
        print(f"[DEBUG] 跳过Gemini分析: use_gemini={use_gemini}, _model={_model}, text_len={len(raw_text) if raw_text else 0}")
        return None
    # 限制输入长度，避免超出 token 限制
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
    try:
        resp = _model.generate_content(prompt)
        print(f"[DEBUG] Gemini 响应: {resp}")
        cands = getattr(resp, "candidates", None) or []
        print(f"[DEBUG] 候选数量: {len(cands)}")
        if not cands or not getattr(cands[0], "content", None):
            print("[DEBUG] 无有效候选或内容")
            return None
        parts = getattr(cands[0].content, "parts", None) or []
        texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
        raw = "\n".join(texts).strip()
        print(f"[DEBUG] 提取的文本: {raw[:500]}...")
        if not raw:
            print("[DEBUG] 提取的文本为空")
            return None
            
        # 清理可能的markdown格式
        clean_json = raw.strip()
        if clean_json.startswith('```json'):
            clean_json = clean_json[7:]
        if clean_json.startswith('```'):
            clean_json = clean_json[3:]
        if clean_json.endswith('```'):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()
        
        print(f"[DEBUG] 清理后的JSON: {clean_json}")
        data = json.loads(clean_json)
        print(f"[DEBUG] 解析的 JSON: {data}")
        # 简单校验
        if "suggestedParts" not in data or not isinstance(data["suggestedParts"], list):
            print("[DEBUG] JSON 格式不符合预期")
            return None
        return data
    except Exception as e:
        print(f"[DEBUG] Gemini 调用异常: {e}")
        import traceback
        traceback.print_exc()
        return None