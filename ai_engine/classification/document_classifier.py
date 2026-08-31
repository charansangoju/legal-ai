KEYWORDS={"employment":["employee","employer","salary","termination"],"nda":["confidential","disclosure","confidentiality"],"loan":["borrower","lender","interest","repayment"],"rental":["tenant","landlord","rent","premises"]}
def classify(text:str)->str:
    t=text.lower()
    scores={k:sum(w in t for w in words) for k,words in KEYWORDS.items()}
    return max(scores,key=scores.get) if max(scores.values(),default=0)>0 else "unknown"
