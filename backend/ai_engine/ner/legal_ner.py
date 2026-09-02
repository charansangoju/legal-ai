import re
def extract_entities(text:str):
    return {"emails":re.findall(r"[\w.+-]+@[\w.-]+",text),"dates":re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",text)}
