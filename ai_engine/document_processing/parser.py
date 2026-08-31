from pathlib import Path
from pypdf import PdfReader
from docx import Document
def parse_file(path: str) -> str:
    p=Path(path)
    try:
        if p.suffix.lower()==".pdf":
            try:
                reader = PdfReader(path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                # Invalid/corrupted PDF -> fallback to text read, error handled upstream
                print(f"[parser] PDF parse failed {p.name}: {e}")
                return ""
        if p.suffix.lower()==".docx":
            try:
                return "\n".join(x.text for x in Document(path).paragraphs)
            except Exception as e:
                print(f"[parser] DOCX parse failed {p.name}: {e}")
                return ""
        return p.read_text(errors="ignore")
    except Exception as e:
        print(f"[parser] fallback read failed {p.name}: {e}")
        return ""
