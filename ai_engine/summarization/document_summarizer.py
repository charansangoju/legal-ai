import re
def summarize(text, max_sentences=5):
    s=[x.strip() for x in re.split(r"(?<=[.!?])\s+",text) if x.strip()]
    return " ".join(s[:max_sentences])
