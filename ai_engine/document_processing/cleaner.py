import re
def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
