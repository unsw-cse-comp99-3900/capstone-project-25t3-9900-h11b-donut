# pyright: reportMissingImports=false
from typing import Optional
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """使用 pypdf 提取 PDF 纯文本；失败返回 None。"""
    try:
        from pypdf import PdfReader  # type: ignore[reportMissingImports]
    except Exception:
        return None
    try:
        path = Path(pdf_path)
        if not path.exists() or not path.is_file():
            return None
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            texts.append(t.strip())
        raw = "\n\n".join(t for t in texts if t)
        return raw if raw.strip() else None
    except Exception:
        return None