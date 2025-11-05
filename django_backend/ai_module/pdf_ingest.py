# pyright: reportMissingImports=false
from typing import Optional
from pathlib import Path
import os

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """使用多种PDF库提取PDF纯文本，支持fallback机制"""
    
    # 路径处理
    try:
        base_dir = Path(__file__).resolve().parent.parent  # == BASE_DIR
        
        # 处理相对路径和绝对路径
        if pdf_path.startswith("/task/"):
            pdf_path = os.path.join(base_dir, "task", pdf_path[len("/task/"):])
        elif pdf_path.startswith("/material/"):
            pdf_path = os.path.join(base_dir, "material", pdf_path[len("/material/"):])
        elif pdf_path.startswith("/media/"):
            pdf_path = os.path.join(base_dir, "media", pdf_path[len("/media/"):])
        elif not os.path.isabs(pdf_path):
            # 如果是相对路径，相对于base_dir
            pdf_path = os.path.join(base_dir, pdf_path)
        
        path = Path(pdf_path)
        print(f'[PDF_INGEST] 尝试读取PDF: {path}')
        
        if not path.exists() or not path.is_file():
            print(f'[PDF_INGEST] PDF文件不存在: {path}')
            return None
            
    except Exception as e:
        print(f'[PDF_INGEST] 路径处理失败: {e}')
        return None
    
    # 方法1: 尝试使用 pypdf
    text = _extract_with_pypdf(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] pypdf提取成功，文本长度: {len(text)}')
        return text
    
    # 方法2: 尝试使用 PyPDF2
    text = _extract_with_pypdf2(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] PyPDF2提取成功，文本长度: {len(text)}')
        return text
    
    # 方法3: 尝试使用 pdfplumber
    text = _extract_with_pdfplumber(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] pdfplumber提取成功，文本长度: {len(text)}')
        return text
    
    # 方法4: 尝试使用 fitz (PyMuPDF)
    text = _extract_with_fitz(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] PyMuPDF提取成功，文本长度: {len(text)}')
        return text
    
    print(f'[PDF_INGEST] 所有PDF提取方法都失败了')
    return None

def _extract_with_pypdf(pdf_path: str) -> Optional[str]:
    """使用pypdf提取文本"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        texts = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                texts.append(text.strip())
            except Exception:
                continue
        result = "\n\n".join(t for t in texts if t)
        return result if result.strip() else None
    except Exception as e:
        print(f'[PDF_INGEST] pypdf失败: {e}')
        return None

def _extract_with_pypdf2(pdf_path: str) -> Optional[str]:
    """使用PyPDF2提取文本"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            texts = []
            for page in reader.pages:
                try:
                    text = page.extract_text() or ""
                    texts.append(text.strip())
                except Exception:
                    continue
            result = "\n\n".join(t for t in texts if t)
            return result if result.strip() else None
    except Exception as e:
        print(f'[PDF_INGEST] PyPDF2失败: {e}')
        return None

def _extract_with_pdfplumber(pdf_path: str) -> Optional[str]:
    """使用pdfplumber提取文本"""
    try:
        import pdfplumber
        texts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    text = page.extract_text() or ""
                    texts.append(text.strip())
                except Exception:
                    continue
        result = "\n\n".join(t for t in texts if t)
        return result if result.strip() else None
    except Exception as e:
        print(f'[PDF_INGEST] pdfplumber失败: {e}')
        return None

def _extract_with_fitz(pdf_path: str) -> Optional[str]:
    """使用PyMuPDF (fitz)提取文本"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        texts = []
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                text = page.get_text() or ""
                texts.append(text.strip())
            except Exception:
                continue
        doc.close()
        result = "\n\n".join(t for t in texts if t)
        return result if result.strip() else None
    except Exception as e:
        print(f'[PDF_INGEST] PyMuPDF失败: {e}')
        return None