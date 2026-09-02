import re
def extract_dates(text): return re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",text)
