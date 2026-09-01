from pathlib import Path
from pypdf import PdfReader
from docx import Document
def parse_file(path: str) -> str:
    p=Path(path)
    try:
        # Universal handling: pdf, docx, doc, txt, and any text-based file
        if p.suffix.lower()==".pdf":
            try:
                reader = PdfReader(path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                if text.strip():
                    return text
                # Scanned PDF fallback - try ocr if available
                try:
                    from ai_engine.document_processing.ocr import run_ocr
                    return run_ocr(str(p))
                except Exception:
                    return text
            except Exception as e:
                print(f"[parser] PDF parse failed {p.name}: {e}")
                # fallback to raw read
                try:
                    return p.read_bytes().decode(errors="ignore")
                except Exception:
                    return ""
        if p.suffix.lower() in (".docx",".doc"):
            try:
                return "\n".join(x.text for x in Document(path).paragraphs)
            except Exception as e:
                print(f"[parser] DOCX parse failed {p.name}: {e}")
                try:
                    return p.read_bytes().decode(errors="ignore")
                except Exception:
                    return ""
        # Any other file (txt, rtf, md, etc.) -> read as text
        try:
            return p.read_text(errors="ignore")
        except Exception:
            return p.read_bytes().decode(errors="ignore")
    except Exception as e:
        print(f"[parser] fallback read failed {p.name}: {e}")
        return ""
