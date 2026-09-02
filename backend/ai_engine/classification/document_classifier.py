KEYWORDS={
    "employment":["employee","employer","salary","termination","employment","job","work","wage"],
    "nda":["confidential","disclosure","confidentiality","non-disclosure","proprietary","secret"],
    "loan":["borrower","lender","interest","repayment","loan","credit","principal","mortgage"],
    "rental":["tenant","landlord","rent","premises","lease","rental","property"],
    "service_agreement":["service","provider","client","deliverable","scope of work","consulting"],
    "partnership":["partnership","partner","joint venture","equity","shareholder"],
    "sales":["purchase","sale","buyer","seller","goods","delivery","invoice","payment"],
    "general_legal":["agreement","contract","clause","party","obligation","terms","conditions","liability"]
}
def classify(text:str)->str:
    t=text.lower()
    scores={k:sum(w in t for w in words) for k,words in KEYWORDS.items()}
    best=max(scores,key=scores.get) if max(scores.values(),default=0)>0 else "unknown"
    # unknown still means analyzable - map to general_legal for UI clarity but keep unknown for backward compat
    if best=="unknown" and len(t.strip())>50:
        # any substantial document is at least general_legal
        return "general_legal"
    return best
