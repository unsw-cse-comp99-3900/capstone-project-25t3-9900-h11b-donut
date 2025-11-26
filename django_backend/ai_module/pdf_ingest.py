# pyright: reportMissingImports=false
from typing import Optional
from pathlib import Path
import os

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract PDF plain text using multiple PDF libraries and support fallback mechanism"""
    
    # handle path
    try:
        base_dir = Path(__file__).resolve().parent.parent  # == BASE_DIR
        
        # Handling relative and absolute paths
        if pdf_path.startswith("/task/"):
            pdf_path = os.path.join(base_dir, "task", pdf_path[len("/task/"):])
        elif pdf_path.startswith("/material/"):
            pdf_path = os.path.join(base_dir, "material", pdf_path[len("/material/"):])
        elif pdf_path.startswith("/media/"):
            pdf_path = os.path.join(base_dir, "media", pdf_path[len("/media/"):])
        elif not os.path.isabs(pdf_path):
            pdf_path = os.path.join(base_dir, pdf_path)
        
        path = Path(pdf_path)
        print(f'[PDF_INGEST] try to read PDF: {path}')
        
        if not path.exists() or not path.is_file():
            print(f'[PDF_INGEST] PDF file not found: {path}')
            return None
            
    except Exception as e:
        print(f'[PDF_INGEST] fail to handle path: {e}')
        return None
    
    # try using pypdf
    text = _extract_with_pypdf(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] pypdf succeed,length: {len(text)}')
        return text
    
    # try using PyPDF2
    text = _extract_with_pypdf2(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] PyPDF2 succeed,length: {len(text)}')
        return text
    
    #try using pdfplumber
    text = _extract_with_pdfplumber(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] pdfplumber succeed,length: {len(text)}')
        return text
    
    # try using fitz (PyMuPDF)
    text = _extract_with_fitz(str(path))
    if text and len(text.strip()) > 50:
        print(f'[PDF_INGEST] PyMuPDF succeed,length: {len(text)}')
        return text
    
    print(f'[PDF_INGEST] All PDF extraction methods have failed')
    return None

def _extract_with_pypdf(pdf_path: str) -> Optional[str]:
    """Extract text using pypdf"""
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
        print(f'[PDF_INGEST] pypdf fail: {e}')
        return None

def _extract_with_pypdf2(pdf_path: str) -> Optional[str]:
    """Extracting Text with PyPDF2"""
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
        print(f'[PDF_INGEST] PyPDF2 fail: {e}')
        return None

def _extract_with_pdfplumber(pdf_path: str) -> Optional[str]:
    """Extracting Text with PDF Lumber"""
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
        print(f'[PDF_INGEST] pdfplumber fail: {e}')
        return None

def _extract_with_fitz(pdf_path: str) -> Optional[str]:
    """Extract text using PyMuPDF (fitz)"""
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
        print(f'[PDF_INGEST] PyMuPDF failed: {e}')
        return None