import re
def extract_obligations(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])",text) if any(x in s.lower() for x in ["shall","must","agrees to","required to"])]
