import tempfile, os
from ai_engine.document_processing.parser import parse_file
from ai_engine.document_processing.cleaner import clean
from ai_engine.classification.document_classifier import classify
def process_upload(upload):
    suffix=os.path.splitext(upload.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as f:
        f.write(upload.file.read()); path=f.name
    try:
        raw = parse_file(path)
        if not raw or not raw.strip():
            # Try direct bytes fallback (plain text PDF mislabel)
            try:
                raw = open(path, encoding="utf-8", errors="ignore").read()
            except Exception:
                raw = ""
        text=clean(raw)
        return text, classify(text)
    finally:
        try: os.unlink(path)
        except Exception: pass
