import re
def extract_money(text): return re.findall(r"(?:₹|\$|Rs\.?)[ ]?[\d,]+(?:\.\d+)?",text)
