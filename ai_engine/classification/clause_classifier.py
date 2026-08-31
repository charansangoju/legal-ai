def classify_clause(text:str)->str:
    t=text.lower()
    for name, words in {"termination":["terminate","termination"],"payment":["payment","salary","rent"],"confidentiality":["confidential"],"liability":["liable","liability"]}.items():
        if any(w in t for w in words): return name
    return "general"
